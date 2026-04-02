import subprocess
import tempfile
import os
from dataclasses import dataclass

@dataclass
class BuildResult:
    success: bool
    error_message: str | None


def build_and_analyze(dockerfile_content: str) -> BuildResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        # 임시 폴더에 Dockerfile 저장
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        # docker build 실행
        result = subprocess.run(
            ["docker", "build", tmpdir],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return BuildResult(success=True, error_message=None)
        else:
            # ERROR: 로 시작하는 줄만 뽑기
            error_lines = [
                line for line in result.stderr.splitlines()
                if "ERROR" in line
            ]
            error_message = "\n".join(error_lines)
            return BuildResult(success=False, error_message=error_message)



