from .base import BaseRule, Instruction, Warning

class RootUserRule(BaseRule):
    def __init__(self):
        self.last_user: str = "root"
        self.last_user_line: int | None = None
        self.last_from_line: int | None = None

    def feed(self, instruction: Instruction) -> None:
        if instruction.name == "FROM":
            self.last_from_line = instruction.line
            self.last_user = "root"
            self.last_user_line = None

        elif instruction.name == "USER":
            parts = instruction.value.split()
            if not parts:
                return
            self.last_user = parts[0].strip().strip("\"'")
            self.last_user_line = instruction.line

    def _is_root(self, user: str) -> bool:
        u = user.lower()
        return (
            u == "root"
            or u == "0"
            or u.startswith("root:")
            or u.startswith("0:")
        )

    def result(self) -> list[Warning]:
        if self.last_from_line is None:
            return []

        if self._is_root(self.last_user):
            line = self.last_user_line or self.last_from_line
            return [
                Warning(
                    rule="root_user",
                    severity="high",
                    line=line,
                    message="USER 명령어가 누락되어 컨테이너가 최고 관리자(root) 권한으로 실행됩니다",
                    why=(
                        "컨테이너와 호스트가 동일한 최고 권한을 공유하게 되어 보안 격리 수준이 낮아집니다. 단일 컨테이너의 취약점이 인프라 전체의 리스크로 전이될 수 있습니다."
                    ),
                    fix=(
                        "전용 사용자를 생성하고 USER 명령어로 전환하세요.\n\n"
                        "RUN <사용자 생성 명령어>\n"
                        "USER <생성한 사용자명>"
                    ),
                    deduction=20,
                )
            ]
        return []
