from .base import BaseRule, Instruction, Warning

FLOATING_TAGS = {"latest", "lts", "current", "stable", "edge", "nightly"}


def _extract_tag(image: str) -> str | None:
    if "@" in image:
        return None
    last_colon = image.rfind(":")
    last_slash = image.rfind("/")
    if last_colon > last_slash:
        return image[last_colon + 1:]
    return None


class LatestTagRule(BaseRule):
    def __init__(self):
        self.warnings: list[Warning] = []

    def feed(self, instruction: Instruction) -> None:
        if instruction.name != "FROM":
            return

        parts = instruction.value.split()
        image_part = next(
            (p for p in parts if not p.startswith("--")), None
        )
        if not image_part:
            return
        if image_part.lower() == "scratch":
            return
        if "@" in image_part:          # digest 이미지는 가장 안전 → 통과
            return
        if image_part.startswith("$"):  # $BASE, ${BASE} 같은 동적 변수는 분석 제외
            return

        tag = _extract_tag(image_part)

        if not tag or tag.lower() in FLOATING_TAGS:
            if not tag:
                message = f"'{image_part}' — 태그가 지정되지 않아 매 빌드마다 다른 이미지가 사용될 수 있습니다"
            else:
                message = f"'{image_part}' — 버전이 고정되지 않은 이미지입니다 (태그: '{tag}')"

            self.warnings.append(
                Warning(
                    rule="latest_tag",
                    severity="high",
                    line=instruction.line,
                    message=message,
                    why=(
                        "버전이 고정되지 않은 이미지는 빌드할 때마다 다른 결과가 나올 수 있습니다. "
                        "이미지가 업데이트되면 예고 없이 동작이 바뀌거나 "
                        "보안 취약점이 포함될 수 있습니다."
                    ),
                    fix=(
                        "이미지 버전을 명확하게 고정하세요.\n\n"
                        "# 권장 방법 1: 구체적인 버전 태그 사용\n"
                        "FROM <이미지>:<버전>\n\n"
                        "# 권장 방법 2: SHA 다이제스트 고정\n"
                        "FROM <이미지>@sha256:<해시값>"
                    ),
                    deduction=15,
                )
            )

    def result(self) -> list[Warning]:
        return self.warnings


