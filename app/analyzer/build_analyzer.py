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
    error_message: str | None


def validate_tag(tag: str) -> bool:
    if len(tag) > 128:      # 128자 초과하면 유효하지 않음
        return False
    pattern = r'^[a-zA-Z0-9\-._:]+$'  # 허용문자
    return bool(re.match(pattern, tag))


def build_and_analyze(dockerfile_content: str, tag: str | None = None) -> BuildResult:
    if tag and not validate_tag(tag):  #태그가 있으면 유효성 검사
        return BuildResult(
            success=False,
            build_time_seconds=None,
            image_size_mb=None,
            image_id=None,
            error_message="유효하지 않은 태그입니다. 영문, 숫자, -, ., _ 만 사용 가능하고 128자 이하여야 합니다."
        )

    with tempfile.TemporaryDirectory() as tmpdir:  # 임시폴더 생성
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)  #도커파일 내용 저장

        start = time.time()  # 빌드 시작 시간 기록

        command = ["docker", "build", tmpdir]  #기본 빌드
        if tag:
            command = ["docker", "build", "-t", tag, tmpdir] # 태그있으면 옵션 추가
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        build_time = round(time.time() - start, 2)  #빌드 소요시간 (소수점 2자리)

        if result.returncode == 0:
            return BuildResult(
                success=True,
                build_time_seconds=build_time,
                image_size_mb=None,
                image_id=None,
                error_message=None
            )
        else:
            return BuildResult(
                success=False,
                build_time_seconds=build_time,
                image_size_mb=None,
                image_id=None,
                error_message=result.stderr
            )