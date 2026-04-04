import re
from .base import BaseRule, Instruction, Warning


# 명백한 빌드 산출물 생성 커맨드 목록
# startswith()로 검사하므로 순서 의미 없음
# pip install, npm install 같은 의존성 설치는 의도적으로 제외
# 모든 prefix는 소문자로 작성할 것 (value.lower()와 비교하므로)
BUILD_PREFIXES = [
    "npm run build", "yarn build", "pnpm build",  # Node.js
    "tsc", "webpack", "vite build", "rollup",      # Frontend 번들러
    "python setup.py build", "python -m build",    # Python 패키징
    "go build",                                    # Go
    "mvn package", "mvn clean package",            # Java Maven
    "gradle build", "./gradlew",                   # Java Gradle (prefix만 체크 — task 순서 다양)
    "cargo build",                                 # Rust
    "dotnet publish",                              # .NET
    "make",                                        # C/C++, 범용 빌드 시스템
]


def _looks_like_build_command(value: str) -> bool:
    # RUN 명령어에서 빌드 산출물 생성 커맨드가 있는지 판단
    # 알려진 한계: exec form, 환경변수 prefix, quoted string 내부는 감지 못할 수 있음
    commands = re.split(r"&&|\|\||\||;|\n", value.lower())
    for cmd in commands:
        stripped = cmd.strip()
        if any(stripped.startswith(prefix) for prefix in BUILD_PREFIXES):
            return True
    return False


class MultistageRule(BaseRule):
    def __init__(self):
        self.from_count: int = 0
        self.first_line: int | None = None
        self.has_build_command: bool = False

    def feed(self, instruction: Instruction) -> None:
        if instruction.name == "FROM":
            self.from_count += 1
            if self.first_line is None:
                self.first_line = instruction.line

        elif instruction.name == "RUN" and not self.has_build_command:
            if _looks_like_build_command(instruction.value):
                self.has_build_command = True

    def result(self) -> list[Warning]:
        if self.from_count == 1 and self.has_build_command:
            return [
                Warning(
                    rule="multistage",
                    severity="medium",
                    line=self.first_line,
                    message="빌드 단계와 런타임 단계가 분리되지 않았습니다 (단일 스테이지 빌드 사용)",
                    why=(
                        "RUN 명령어에 소스 코드 빌드 과정이 포함되어 있으나, "
                        "단일 스테이지를 사용하여 빌드 도구와 중간 산출물이 "
                        "최종 이미지에 그대로 남습니다."
                    ),
                    fix=(
                        "빌드 스테이지와 실행 스테이지를 분리하세요.\n\n"
                        "# 1단계: 빌드\n"
                        "FROM <빌드 이미지> AS builder\n"
                        "COPY <의존성 파일> ./\n"
                        "RUN <의존성 설치 명령어>\n"
                        "COPY . .\n"
                        "RUN <빌드 명령어>\n\n"
                        "# 2단계: 실행\n"
                        "FROM <경량 이미지>\n"
                        "COPY --from=builder <빌드 결과물 경로> .\n"
                        "CMD [\"<실행 명령어>\"]"
                    ),
                    deduction=15,
                )
            ]
        return []