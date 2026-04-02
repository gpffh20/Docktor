#테스트용
from app.analyzer.build_analyzer import build_and_analyze

with open("test/Dockerfile", "r") as f:
    content = f.read()

result = build_and_analyze(content)
print(result)