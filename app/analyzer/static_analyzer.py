from .rules.base import BaseRule, Instruction, StaticAnalysisResult, Warning
from .rules.latest_tag import LatestTagRule
from .rules.multistage import MultistageRule
from .rules.root_user import RootUserRule
from .rules.healthcheck import HealthcheckRule
from .rules.copy_order import CopyOrderRule


def _strip_inline_comment(value: str) -> str:
    # 주의: 따옴표 내부의 # 은 일부 처리하지만,
    # shell-like value나 복잡한 quoted value는 완벽히 처리하지 못할 수 있음
    in_quote = False
    quote_char = None
    for i, ch in enumerate(value):
        if ch in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif quote_char == ch:
                in_quote = False
        elif ch == "#" and not in_quote:
            return value[:i].strip()
    return value.strip()


def parse_dockerfile(content: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    lines = content.splitlines()
    i = 0

    while i < len(lines):
        raw = lines[i].strip()
        start_line = i + 1

        if not raw or raw.startswith("#"):
            i += 1
            continue

        merged = ""
        incomplete_multiline = False

        while raw.endswith("\\"):
            merged += raw[:-1].strip() + " "
            i += 1
            while i < len(lines):
                next_raw = lines[i].strip()
                if not next_raw or next_raw.startswith("#"):
                    i += 1
                    continue
                break
            if i >= len(lines):
                incomplete_multiline = True
                break
            raw = lines[i].strip()

        if incomplete_multiline:
            break  # EOF에서 끊긴 불완전 instruction은 버리고 파싱 종료

        merged += raw

        if merged:
            parts = merged.split(maxsplit=1)
            name = parts[0].upper()
            value = parts[1] if len(parts) > 1 else ""
            if name not in {"RUN", "CMD", "ENTRYPOINT"}:
                value = _strip_inline_comment(value)
            instructions.append(
                Instruction(line=start_line, name=name, value=value)
            )

        i += 1

    return instructions


def analyze(dockerfile_content: str) -> StaticAnalysisResult:
    instructions = parse_dockerfile(dockerfile_content)

    rules: list[BaseRule] = [
        LatestTagRule(),
        MultistageRule(),
        RootUserRule(),
        HealthcheckRule(),
        CopyOrderRule(),
    ]

    base_image: str = "unknown"
    base_images: list[str] = []
    is_first_from = False

    for inst in instructions:
        if inst.name == "FROM" and not is_first_from:
            parts = inst.value.split()
            candidate = next(
                (p for p in parts if not p.startswith("--")), None
            )
            if candidate:
                if candidate.startswith("$"):
                    base_image = "unknown"
                else:
                    base_image = candidate.split("@", 1)[0]
            is_first_from = True
        if inst.name == "FROM":
            parts = inst.value.split()
            candidate = next(
                (p for p in parts if not p.startswith("--")), None
            )
            if candidate:
                if candidate.startswith("$"):
                    base_images.append("unknown")
                else:
                    base_images.append(candidate.split("@", 1)[0])
        for rule in rules:
            rule.feed(inst)

    warnings: list[Warning] = []
    for rule in rules:
        warnings.extend(rule.result())

    warnings.sort(
        key=lambda w: (-w.deduction, w.line if w.line is not None else 9999)
    )

    if not base_images:
        base_images = [base_image]

    return StaticAnalysisResult(
        warnings=warnings,
        base_image=base_image,
        base_images=base_images,
    )
