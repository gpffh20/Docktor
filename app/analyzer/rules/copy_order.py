import fnmatch
from .base import BaseRule, Instruction, Warning


DEP_FILES = {
    "requirements.txt", "pyproject.toml", "pipfile", "poetry.lock",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "go.mod", "go.sum", "gemfile", "gemfile.lock",
    "pom.xml", "build.gradle", "build.gradle.kts"
}


class CopyOrderRule(BaseRule):
    def __init__(self):
        self.copy_all_line: int | None = None
        self.dep_copy_line: int | None = None
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
        if (
            self.copy_all_line is not None
            and self.dep_copy_line is not None
            and self.copy_all_line < self.dep_copy_line
        ):
            self.warnings.append(
                Warning(
                    rule="copy_order",
                    severity="medium",
                    line=self.copy_all_line,
                    message="전체 소스 복사가 의존성 파일 복사보다 먼저 수행됩니다",
                    why=(
                        "의존성 파일을 기준으로 별도 설치 레이어를 두는 Dockerfile에서는, "
                        "전체 소스를 먼저 복사할 경우 캐시 효율이 떨어질 수 있습니다."
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

    def result(self) -> list[Warning]:
        if not self.saw_from:
            return []
        if not self.finalized:
            self._flush_stage()
            self.finalized = True
        return self.warnings