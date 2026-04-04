import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from app.analyzer.static_analyzer import analyze
from app.analyzer.build_analyzer import build_and_analyze
from app.scorer.calculator import calculate
from app.reporter import console as console_reporter
from app.reporter import json_report

app = typer.Typer(help="Docktor — Your Dockerfile Doctor", add_completion=False)

def _load(path: Path) -> str:
    if not path.exists():
        typer.echo(f"파일을 찾을 수 없습니다: {path}", err=True)
        raise typer.Exit(2)
    return path.read_text()




@app.command(name="analyze")
def analyze_cmd(
    file: Annotated[Path, typer.Option("--file", "-f", help="분석할 Dockerfile 경로")],
    build: Annotated[bool, typer.Option("--build", help="실제 docker build 실행")] = False,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="빌드 태그 (예: myapp:test)")] = None,
    format: Annotated[str, typer.Option("--format", help="출력 형식: text | json")] = "text",
):
    """Dockerfile을 정적 분석하고 선택적으로 빌드합니다."""
    content = _load(file)
    static = analyze(content)

    build_result = None
    if build:
        build_result = build_and_analyze(content, tag=tag)

    score_result = calculate(static.warnings, build_result)

    if format == "json":
        typer.echo(json_report.to_json(static, score_result, build_result))
    else:
        console_reporter.print_report(static, score_result, build_result, str(file))

    sys.exit({"Good": 0, "Warning": 1, "Risky": 2}[score_result.grade])


@app.command()
def compare(
    before: Annotated[Path, typer.Option("--before", help="비교 전 Dockerfile 경로")],
    after: Annotated[Path, typer.Option("--after", help="비교 후 Dockerfile 경로")],
    build: Annotated[bool, typer.Option("--build", help="두 Dockerfile 모두 빌드")] = False,
    format: Annotated[str, typer.Option("--format", help="출력 형식: text | json")] = "text",
):
    """두 Dockerfile의 Before/After 결과를 비교합니다."""
    content_b = _load(before)
    content_a = _load(after)

    static_b = analyze(content_b)
    static_a = analyze(content_a)

    build_result_b = None
    build_result_a = None
    if build:
        build_result_b = build_and_analyze(content_b)
        build_result_a = build_and_analyze(content_a)

    score_b = calculate(static_b.warnings, build_result_b)
    score_a = calculate(static_a.warnings, build_result_a)

    if format == "json":
        typer.echo(json_report.compare_to_json(static_b, score_b, build_result_b, static_a, score_a, build_result_a))
    else:
        console_reporter.print_compare(static_b, score_b, build_result_b, static_a, score_a, build_result_a, str(before), str(after))

    if build_result_a is not None and not build_result_a.success:
        sys.exit(2)


if __name__ == "__main__":
    app()
