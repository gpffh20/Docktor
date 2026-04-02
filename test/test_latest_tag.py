import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "analyzer", "rules"))

from base import BaseRule, Instruction, Warning
from latest_tag import LatestTagRule


def main():
    dockerfile = """
FROM node:latest
RUN npm install
COPY . .
FROM python:3.12-slim
CMD ["python", "app.py"]
"""

    rule = LatestTagRule()

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

    warnings = rule.result()

    print(f"감지된 경고 수: {len(warnings)}\n")
    for w in warnings:
        print(f"[{w.severity.upper()}] Line {w.line}: {w.message}")
        print(f"  왜?: {w.why}")
        print(f"  감점: -{w.deduction}점\n")


if __name__ == "__main__":
    main()