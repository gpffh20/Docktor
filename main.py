import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from app.analyzer.static_analyzer import analyze
from app.analyzer.build_analyzer import build_and_analyze

app = typer.Typer(help="Docktor — Docker Image Quality Gate", add_completion=False)


def _load(path: Path) -> str:
    if not path.exists():
        typer.echo(f"파일을 찾을 수 없습니다: {path}", err=True)
        raise typer.Exit(2)
    return path.read_text()


def _print_static(result) -> None:
    typer.echo(f"베이스 이미지: {result.base_image}\n")
    total_deduction = 0
    for w in result.warnings:
        typer.echo(f"[{w.severity.upper()}] Line {w.line}: {w.message}")
        typer.echo(f"  규칙: {w.rule}")
        typer.echo(f"  왜?: {w.why}")
        typer.echo(f"  감점: -{w.deduction}점\n")
        total_deduction += w.deduction
    score = max(0, 100 - total_deduction)
    typer.echo(f"최종 점수: {score}점 (총 감점: -{total_deduction}점)")


def _print_build(build_result) -> None:
    typer.echo(build_result)


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
    _print_static(static)

    build_result = None
    if build:
        build_result = build_and_analyze(content, tag=tag)
        _print_build(build_result)

    if build_result is not None and not build_result.success:
        sys.exit(2)
    elif static.warnings:
        sys.exit(1)
    else:
        sys.exit(0)


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

    typer.echo("── BEFORE ──────────────────────────────")
    _print_static(static_b)
    if build:
        _print_build(build_and_analyze(content_b))

    typer.echo("── AFTER ───────────────────────────────")
    _print_static(static_a)
    if build:
        build_a = build_and_analyze(content_a)
        _print_build(build_a)
        if not build_a.success:
            sys.exit(2)


if __name__ == "__main__":
    app()
