import subprocess
import tempfile
import os
import time
import re
from dataclasses import dataclass

@dataclass
class BuildResult:
    success: bool
    build_time_seconds: float | None
    image_size_mb: float | None
    image_id: str | None
    tag: str | None
    error_message: str | None


def validate_tag(tag: str) -> bool:
    if len(tag) > 128:      # 128자 초과하면 유효하지 않음
        return False
    pattern = r'^[a-zA-Z0-9\-._:]+$'  # 허용문자
    return bool(re.match(pattern, tag))


def build_and_analyze(dockerfile_content: str, tag: str | None = None) -> BuildResult:
    if tag and not validate_tag(tag):  # 태그가 있으면 유효성 검사
        return BuildResult(
            success=False,
            build_time_seconds=None,
            image_size_mb=None,
            image_id=None,
            tag=tag,
            error_message="유효하지 않은 태그입니다. 영문, 숫자, -, ., _ 만 사용 가능하고 128자 이하여야 합니다."
        )

    with tempfile.TemporaryDirectory() as tmpdir:  # 임시폴더 생성 (with 블록 끝나면 자동 삭제)
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")  # 임시폴더 안에 Dockerfile 경로 지정
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)  # Dockerfile 내용 저장

        iid_file = os.path.join(tmpdir, "iid.txt")  # 이미지 ID 저장할 파일 경로

        start = time.time()  # 빌드 시작 시간 기록

        command = ["docker", "build", "--iidfile", iid_file, tmpdir]  # 기본 빌드
        if tag:
            command = ["docker", "build", "--iidfile", iid_file, "-t", tag, tmpdir]  # 태그있으면 옵션 추가

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
                error_message=None
            )
        else:
            return BuildResult(
                success=False,
                build_time_seconds=build_time,
                image_size_mb=None,
                image_id=None,
                tag=tag,
                error_message=result.stderr
            )