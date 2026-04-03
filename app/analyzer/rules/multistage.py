from .base import BaseRule, Instruction, Warning


class MultistageRule(BaseRule):
    def __init__(self):
        self.from_count: int = 0
        self.first_line: int | None = None

    def feed(self, instruction: Instruction) -> None:
        if instruction.name == "FROM":
            self.from_count += 1
            if self.first_line is None:
                self.first_line = instruction.line

    def result(self) -> list[Warning]:
        if self.from_count == 1:
            return [
                Warning(
                    rule="multistage",
                    severity="medium",
                    line=self.first_line,
                    message="멀티스테이지 빌드가 적용되지 않았습니다 (단일 스테이지 빌드 사용)",
                    why=(
                        "빌드 도구와 소스 코드가 최종 이미지에 남아 용량이 커지고, 운영 및 보안 관리 부담이 커질 수 있습니다."
                    ),
                    fix=(
                        "빌드 스테이지와 실행 스테이지를 분리하세요.\n\n"
                        "# 1단계: 빌드\n"
                        "FROM <빌드 이미지> AS builder\n"
                        "WORKDIR /app\n"
                        "COPY <의존성 파일> ./\n"
                        "RUN <의존성 설치 명령어>\n"
                        "COPY . .\n"
                        "RUN <빌드 명령어>\n\n"
                        "# 2단계: 실행\n"
                        "FROM <경량 이미지>\n"
                        "WORKDIR /app\n"
                        "COPY --from=builder <빌드 결과물 경로> .\n"
                        "CMD [\"<실행 명령어>\"]"
                    ),
                    deduction=15,
                )
            ]
        return []


