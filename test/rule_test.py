from app.analyzer.static_analyzer import analyze
import sys


def main():
    if len(sys.argv) < 2:
        print("사용법: py -m test.rule_test <Dockerfile 경로>")
        return

    path = sys.argv[1]

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    result = analyze(content)

    print(f"베이스 이미지: {result.base_image}\n")

    total_deduction = 0
    for w in result.warnings:
        print(f"[{w.severity.upper()}] Line {w.line}: {w.message}")
        print(f"  규칙: {w.rule}")
        print(f"  왜?: {w.why}")
        print(f"  감점: -{w.deduction}점\n")
        total_deduction += w.deduction

    score = max(0, 100 - total_deduction)
    print(f"최종 점수: {score}점 (총 감점: -{total_deduction}점)")


if __name__ == "__main__":
    main()