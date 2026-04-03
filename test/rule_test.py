from app.analyzer.rules.base import Instruction
from app.analyzer.rules.latest_tag import LatestTagRule
from app.analyzer.rules.multistage import MultistageRule
from app.analyzer.rules.root_user import RootUserRule
from app.analyzer.rules.healthcheck import HealthcheckRule
from app.analyzer.rules.copy_order import CopyOrderRule


def run_rule(rule, dockerfile: str):
    for i, line in enumerate(dockerfile.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) < 2:
            continue
        name = parts[0].upper()
        value = parts[1]
        instruction = Instruction(line=i, name=name, value=value)
        rule.feed(instruction)
    return rule.result()


def main():
    dockerfile = """
FROM node:latest
COPY . .
COPY package.json ./
RUN npm install
CMD ["node", "app.js"]
"""

    rules = [
        ("latest_tag", LatestTagRule()),
        ("multistage", MultistageRule()),
        ("root_user", RootUserRule()),
        ("healthcheck", HealthcheckRule()),
        ("copy_order", CopyOrderRule()),
    ]

    total_deduction = 0

    for name, rule in rules:
        warnings = run_rule(rule, dockerfile)
        for w in warnings:
            print(f"[{w.severity.upper()}] Line {w.line}: {w.message}")
            print(f"  규칙: {w.rule}")
            print(f"  왜?: {w.why}")
            print(f"  감점: -{w.deduction}점\n")
            total_deduction += w.deduction

    score = max(0, 100 - total_deduction)
    print(f"최종 점수: {score}점 (총 감점: -{total_deduction}점)")


if __name__ == "__main__":
    main()