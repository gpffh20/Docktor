try:
    from .base import BaseRule, Instruction, Warning
except ImportError:
    from base import BaseRule, Instruction, Warning


class HealthcheckRule(BaseRule):
    def __init__(self):
        self.has_healthcheck: bool = False
        self.disabled_by_none: bool = False
        self.last_from_line: int | None = None
        self.last_healthcheck_line: int | None = None

    def feed(self, instruction: Instruction) -> None:
        if instruction.name == "FROM":
            self.has_healthcheck = False
            self.disabled_by_none = False
            self.last_from_line = instruction.line
            self.last_healthcheck_line = None
        elif instruction.name == "HEALTHCHECK":
            value = instruction.value.strip().upper()
            self.disabled_by_none = value == "NONE"
            self.has_healthcheck = bool(value) and not self.disabled_by_none
            self.last_healthcheck_line = instruction.line

    def result(self) -> list[Warning]:
        if self.last_from_line is None:
            return []

        if not self.has_healthcheck:
            if self.disabled_by_none:
                message = "최종 스테이지에서 HEALTHCHECK가 비활성화되었습니다"
                line = self.last_healthcheck_line or self.last_from_line
            else:
                message = "최종 스테이지에 HEALTHCHECK 명령어가 없습니다"
                line = self.last_from_line

            return [
                Warning(
                    rule="healthcheck",
                    severity="medium",
                    line=line,
                    message=message,
                    why=(
                        "컨테이너 프로세스가 실행 중이더라도, 애플리케이션의 실제 무응답 상태를 파악할 수 없습니다. "
                        "시스템이 비정상 상태를 인지하지 못해 장애가 발생한 컨테이너로 트래픽이 전달될 수 있습니다. "
                    ),
                    fix=(
                        "HEALTHCHECK 명령어를 추가하여 컨테이너 상태를 주기적으로 확인하세요.\n\n"
                        "HEALTHCHECK --interval=<검사 주기> --timeout=<타임아웃> --retries=<재시도 횟수> \\\n"
                        "  CMD <헬스체크 명령어>"
                    ),
                    deduction=10,
                )
            ]
        return []


