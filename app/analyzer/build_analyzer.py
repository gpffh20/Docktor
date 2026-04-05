import subprocess
import tempfile
import os
import time
import re
import json
import shutil
import tarfile
from datetime import datetime
from dataclasses import dataclass

@dataclass
class BuildResult:
    success: bool
    build_time_seconds: float | None
    image_size_mb: float | None
    image_id: str | None
    tag: str | None
    base_images: list[str] | None
    cache_summary: str | None
    security_issues: list[str] | None
    error_message: str | None


def _parse_cache_summary(raw_stderr: str) -> str | None:
    layers = []

    for line in raw_stderr.splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        for vertex in data.get("vertexes", []):
            name = vertex.get("name", "")
            started = vertex.get("started")  #레이어 시작 시간
            completed = vertex.get("completed") #레이어 완료 시간
            cached = vertex.get("cached", False) #캐시 사용 여부

            if started and completed:
                start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
                duration = round((end_dt - start_dt).total_seconds(), 2)
                layers.append((name, duration, cached))

    # [1/3] 같은 실제 레이어만 필터링하고 FROM은 제외
    real_layers = [(name, duration, cached) for name, duration, cached in layers
                   if re.match(r'^\[\d+/\d+\]', name)
                   and "FROM" not in name]
    # 캐시 안 된 첫 번째 레이어 찾기
    cache_break = None
    wasted_time = 0.0
    for name, duration, cached in real_layers:
        if not cached and cache_break is None:
            cache_break = name
        if cache_break and not cached:
            wasted_time += duration

    if cache_break:
        return f"'{cache_break}'에서 캐시가 깨졌습니다. COPY 순서 변경 시 약 {round(wasted_time, 2)}초 절약 가능합니다."
    return None  #캐시 정상이면 None 반환

# 탐지할 크리덴셜 파일 패턴 (시스템 CA 인증서 제외)
CREDENTIAL_PATTERNS = {
    ".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    ".p12", ".pfx"
    # .pem, .key, .crt 제거 → 시스템 CA 인증서 오탐 방지
}
# SUID/SGID 화이트리스트
SUID_WHITELIST = {
    "usr/bin/sudo", "usr/bin/passwd", "usr/bin/newgrp",
    "usr/bin/gpasswd", "usr/bin/chsh", "usr/bin/chfn",
    "usr/bin/su", "usr/bin/mount", "usr/bin/umount",
    "usr/bin/newuidmap", "usr/bin/newgidmap",
    "usr/bin/chage", "usr/bin/expiry",
    "usr/sbin/unix_chkpwd",
}
SYSTEM_CA_PATHS = (
    "etc/ssl/",
    "usr/share/ca-certificates/",
    "usr/lib/ssl/",
    "usr/local/lib/python",
)

def _check_file(f, norm_path, basename, file_seen, issues, seen):
    # ghost file
    if basename.startswith(".wh."):
        dir_part = os.path.dirname(norm_path)
        original_path = os.path.join(dir_part, basename[len(".wh."):]).lstrip("/")
        if file_seen.get(original_path) == "exists":
            _add(issues, seen, f"ghost file 발견: /{original_path} (이전 레이어에 존재, 이후 삭제됨)")
        file_seen[original_path] = "deleted"
        return

    file_seen[norm_path] = "exists"

    if f.issym() or f.islnk() or not f.isfile():
        return

    if f.mode & 0o4000 and norm_path not in SUID_WHITELIST:
        _add(issues, seen, f"SUID 파일 발견: /{norm_path}")
    if f.mode & 0o2000 and norm_path not in SUID_WHITELIST:
        _add(issues, seen, f"SGID 파일 발견: /{norm_path}")

    if not any(norm_path.startswith(p) for p in SYSTEM_CA_PATHS):
        if f.mode & 0o002:
            _add(issues, seen, f"world-writable 파일 발견: /{norm_path}")
        fname = basename.lower()
        for pattern in CREDENTIAL_PATTERNS:
            if fname == pattern or fname.endswith(pattern):
                _add(issues, seen, f"크리덴셜 파일 발견: /{norm_path}")
                break


def _add(issues, seen, issue):
    if issue not in seen:
        issues.append(issue)
        seen.add(issue)


def _analyze_security(image_id: str) -> list[str]:
    issues, seen, file_seen = [], set(), {}

    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = os.path.join(tmpdir, "image.tar")

        save = subprocess.run(
            ["docker", "save", image_id, "-o", tar_path],
            capture_output=True, text=True
        )
        if save.returncode != 0:
            return []

        with tarfile.open(tar_path) as outer:
            # ── manifest.json에서 레이어 순서 읽기 ──
            manifest_file = outer.extractfile("manifest.json")
            if not manifest_file:
                return []
            manifest = json.load(manifest_file)
            ordered_layers = manifest[0].get("Layers", [])  # 실제 순서대로 된 레이어 경로 목록

            # ── 순서대로 레이어 순회 ──
            for layer_path in ordered_layers:
                layer_file = outer.extractfile(layer_path)
                if not layer_file:
                    continue
                try:
                    with tarfile.open(fileobj=layer_file) as inner:
                        for f in inner.getmembers():
                            norm_path = f.name.lstrip("./")
                            basename = os.path.basename(norm_path)
                            _check_file(f, norm_path, basename, file_seen, issues, seen)
                except tarfile.TarError:
                    continue

    return issues

def validate_tag(tag: str) -> bool:
    if len(tag) > 128:      # 128자 초과하면 유효하지 않음
        return False
    pattern = r'^[a-zA-Z0-9\-._:]+$'  # 허용문자
    return bool(re.match(pattern, tag))


def build_and_analyze(dockerfile_content: str, tag: str | None = None) -> BuildResult:
    #FROM 라인에서 base image 추출
    base_images = []
    stage = 1
    for line in dockerfile_content.splitlines():
        if line.strip().startswith("FROM"):  #FROM으로 시작하는 줄 찾기
            image = line.split()[1]
            base_images.append(f"stage{stage}: {image}")  # 스테이지 번호와 함께 추가
            stage += 1
    if tag and not validate_tag(tag):  # 태그가 있으면 유효성 검사
        return BuildResult(
            success=False,
            build_time_seconds=None,
            image_size_mb=None,
            image_id=None,
            tag=tag,
            base_images=base_images,
            cache_summary=None,
            security_issues=None,
            error_message="유효하지 않은 태그입니다. 영문, 숫자, -, ., _ 만 사용 가능하고 128자 이하여야 합니다."
        )

    with tempfile.TemporaryDirectory() as tmpdir:  # 임시폴더 생성 (with 블록 끝나면 자동 삭제)
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")  # 임시폴더 안에 Dockerfile 경로 지정
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)  # Dockerfile 내용 저장

            # build context 파일들 복사 (requirements.txt 등)-임시용
        for file in os.listdir("test"):
            src = os.path.join("test", file)
            if os.path.isfile(src) and not file.startswith("Dockerfile"):
                shutil.copy(src, tmpdir)

        iid_file = os.path.join(tmpdir, "iid.txt")  # 이미지 ID 저장할 파일 경로

        start = time.time()  # 빌드 시작 시간 기록

        command = ["docker", "build", "--progress=rawjson", "--iidfile", iid_file, tmpdir] # 기본 빌드
        if tag:
            command = ["docker", "build", "--progress=rawjson", "--iidfile", iid_file, "-t", tag, tmpdir] #태그 있는 빌드

        result = subprocess.run(
            command,
            capture_output=True,  # stdout, stderr 캡처
            text=True             # 문자열로 반환
        )

        build_time = round(time.time() - start, 2)  # 빌드 소요시간 (소수점 2자리)

        if result.returncode == 0:
            # iid 파일에서 이미지 ID 읽기
            with open(iid_file, "r") as f:
                image_id = f.read().strip()

            issues = _analyze_security(image_id)

            # docker inspect로 이미지 크기 가져오기 (bytes → MB 변환)
            inspect = subprocess.run(
                ["docker", "inspect", "--format", "{{.Size}}", image_id],
                capture_output=True,
                text=True
            )
            image_size_mb = round(int(inspect.stdout.strip()) / (1024 * 1024), 2)

            return BuildResult(
                success=True,
                build_time_seconds=build_time,
                image_size_mb=image_size_mb,
                image_id=image_id,
                tag=tag,
                base_images=base_images,
                cache_summary=_parse_cache_summary(result.stderr),
                security_issues=issues,
                error_message=None
            )
        else:
            #ERROR 포함된 줄만 뽑기
            error_lines = [line for line  in result.stderr.splitlines() if "ERROR" in line]
            error_message = "\n".join(error_lines) if error_lines else result.stderr #에러 줄 없으면 전체 출력
            return BuildResult(
                success=False,
                build_time_seconds=build_time,
                image_size_mb=None,
                image_id=None,
                tag=tag,
                base_images=base_images,
                cache_summary= None,
                security_issues=None,
                error_message=error_message
            )