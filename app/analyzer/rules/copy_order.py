import re
import fnmatch
from .base import BaseRule, Instruction, Warning


DEP_FILES = {
    "requirements.txt", "pyproject.toml", "pipfile", "poetry.lock",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "go.mod", "go.sum", "gemfile", "gemfile.lock",
    "pom.xml", "build.gradle", "build.gradle.kts"
}

INSTALL_PREFIXES = [
    "pip install", "pip3 install", "pipx install", "poetry install",
    "npm install", "npm ci", "yarn install", "pnpm install",
    "go mod download",
    "bundle install",
    "mvn dependency:go-offline",
]


def _is_install_command(value: str) -> bool:
    commands = re.split(r"&&|\|\||\||;|\n", value.lower())
    for cmd in commands:
        stripped = cmd.strip()
        if any(stripped.startswith(prefix) for prefix in INSTALL_PREFIXES):
            return True
    return False


class CopyOrderRule(BaseRule):
    def __init__(self):
        self.copy_all_line: int | None = None
        self.dep_copy_line: int | None = None
        self.install_run_lines: list[int] = []
        self.warnings: list[Warning] = []
        self.finalized: bool = False
        self.saw_from: bool = False

    def _is_copy_all(self, clean: str) -> bool:
        parts = clean.split()
        actual_parts = [p for p in parts if not p.startswith("--")]
        if not actual_parts:
            return False
        src = actual_parts[0]
        return src in (".", "./", "*")

    def _is_dep_file(self, clean: str) -> bool:
        parts = [p for p in clean.lower().split() if not p.startswith("--")]
        if len(parts) < 2:
            return False
        src_tokens = parts[:-1]  # 마지막은 destination 제외

        for token in src_tokens:
            basename = token.split("/")[-1]  # 경로에서 파일명만 추출
            if (
                basename in DEP_FILES
                or fnmatch.fnmatch(basename, "requirements*.txt")
                or fnmatch.fnmatch(basename, "package*.json")
            ):
                return True
        return False

    def _flush_stage(self) -> None:
        # 설치 RUN이 없으면 캐시 최적화 문제가 없음 → 통과
        if not self.install_run_lines:
            return

        # 전체 복사가 없으면 검사 불필요 → 통과
        if self.copy_all_line is None:
            return

        # COPY . . 이후에 설치 명령이 없으면 캐시 파괴 문제 없음 → 통과
        if not any(line > self.copy_all_line for line in self.install_run_lines):
            return

        # 여기까지 왔다는 것은 COPY . . 이후에 설치 명령이 반드시 존재한다는 뜻
        is_violation = False

        if self.dep_copy_line is not None:
            # 정상 패턴: dep_copy → install_run → copy_all
            # dep_copy와 copy_all 사이에 설치 명령이 하나라도 있으면 정상으로 간주
            # 로컬 패키지 후행 설치(pip install -e .) 같은 케이스는 허용
            has_valid_install = any(
                self.dep_copy_line < line < self.copy_all_line
                for line in self.install_run_lines
            )
            if not has_valid_install:
                is_violation = True
        else:
            # 의존성 파일 복사 없이 전체 복사 이후에 설치하는 경우
            # 방어선을 통과했으므로 100% 위반
            is_violation = True

        if is_violation:
            self.warnings.append(
                Warning(
                    rule="copy_order",
                    severity="medium",
                    line=self.copy_all_line,
                    message="전체 소스 복사가 의존성 설치보다 먼저 수행됩니다",
                    why=(
                        "의존성 파일을 먼저 복사하고 설치한 뒤 소스 코드를 복사해야 "
                        "소스 코드가 변경되어도 의존성 설치 레이어 캐시가 유지됩니다. "
                        "현재 구조에서는 소스 코드가 변경될 때마다 패키지를 다시 설치하게 될 수 있습니다."
                    ),
                    fix=(
                        "의존성 파일을 먼저 복사하고 설치한 뒤 소스 코드를 복사하세요.\n\n"
                        "COPY <의존성 파일> ./\n"
                        "RUN <의존성 설치 명령어>\n"
                        "COPY . ."
                    ),
                    deduction=10,
                )
            )

    def feed(self, instruction: Instruction) -> None:
        if instruction.name == "FROM":
            self.saw_from = True
            self._flush_stage()
            self.copy_all_line = None
            self.dep_copy_line = None
            self.install_run_lines = []

        elif instruction.name == "COPY":
            if "--from=" in instruction.value.lower():
                return

            clean = (
                instruction.value
                .replace('"', '')
                .replace("'", '')
                .replace('[', '')
                .replace(']', '')
                .replace(',', ' ')
            )

            if self._is_copy_all(clean) and self.copy_all_line is None:
                self.copy_all_line = instruction.line

            if self._is_dep_file(clean) and self.dep_copy_line is None:
                self.dep_copy_line = instruction.line

        elif instruction.name == "RUN":
            if _is_install_command(instruction.value):
                self.install_run_lines.append(instruction.line)

    def result(self) -> list[Warning]:
        if not self.saw_from:
            return []
        if not self.finalized:
            self._flush_stage()
            self.finalized = True
        return self.warnings