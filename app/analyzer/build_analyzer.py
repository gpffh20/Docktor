import subprocess
import tempfile
import os
import time
from dataclasses import dataclass

@dataclass
class BuildResult:
    success: bool
    build_time_seconds: float | None
    image_size_mb: float | None
    image_id: str | None
    error_message: str | None


def build_and_analyze(dockerfile_content: str, tag: str | None = None) -> BuildResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        start = time.time()  # 시작 직전 시간 기록

        command = ["docker", "build", tmpdir]
        if tag:
            command = ["docker", "build", "-t", tag, tmpdir]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        build_time = round(time.time() - start, 2)  # 끝난 시간 - 시작시간 = 걸린시간(소숫점 두자리까지)

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