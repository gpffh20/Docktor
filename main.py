from app.analyzer.build_analyzer import build_and_analyze

with open("test/Dockerfile", "r") as f:
    content = f.read()

tag = input("태그 입력 : ").strip() or None

result = build_and_analyze(content, tag=tag)
print(result)