import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from app.analyzer.static_analyzer import analyze
from app.analyzer.build_analyzer import build_and_analyze
from app.analyzer.security_analyzer import scan_config, scan_image
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
    trivy: Annotated[bool, typer.Option("--trivy", help="Trivy 보안 스캔 실행")] = False,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="빌드 태그 (예: myapp:test)")] = None,
    format: Annotated[str, typer.Option("--format", help="출력 형식: text | json")] = "text",
):
    """Dockerfile을 정적 분석하고 선택적으로 빌드합니다."""
    content = _load(file)
    static = analyze(content)

    build_result = None
    security_result = None
    if build:
        build_result = build_and_analyze(content, tag=tag, context_root=file.parent)
    if trivy:
        if build_result is not None and build_result.success:
            image_ref = build_result.tag or build_result.image_id
            if image_ref is not None:
                security_result = scan_image(image_ref)
        elif build:
            security_result = None
        else:
            security_result = scan_config(str(file))

    score_result = calculate(static.warnings, build_result, security_result)

    if format == "json":
        typer.echo(json_report.to_json(static, score_result, build_result, security_result))
    else:
        console_reporter.print_report(static, score_result, build_result, security_result, str(file))

    sys.exit({"Good": 0, "Warning": 1, "Risky": 2}[score_result.grade])


@app.command()
def compare(
    before: Annotated[Path, typer.Option("--before", help="비교 전 Dockerfile 경로")],
    after: Annotated[Path, typer.Option("--after", help="비교 후 Dockerfile 경로")],
    build: Annotated[bool, typer.Option("--build", help="두 Dockerfile 모두 빌드")] = False,
    trivy: Annotated[bool, typer.Option("--trivy", help="Trivy 보안 스캔 실행")] = False,
    format: Annotated[str, typer.Option("--format", help="출력 형식: text | json")] = "text",
):
    """두 Dockerfile의 Before/After 결과를 비교합니다."""
    content_b = _load(before)
    content_a = _load(after)

    static_b = analyze(content_b)
    static_a = analyze(content_a)

    build_result_b = None
    build_result_a = None
    security_result_b = None
    security_result_a = None
    if build:
        build_result_b = build_and_analyze(content_b, context_root=before.parent)
        build_result_a = build_and_analyze(content_a, context_root=after.parent)

    if trivy:
        if build:
            if build_result_b is not None and build_result_b.success:
                image_ref_b = build_result_b.tag or build_result_b.image_id
                if image_ref_b is not None:
                    security_result_b = scan_image(image_ref_b)
            if build_result_a is not None and build_result_a.success:
                image_ref_a = build_result_a.tag or build_result_a.image_id
                if image_ref_a is not None:
                    security_result_a = scan_image(image_ref_a)
        else:
            security_result_b = scan_config(str(before))
            security_result_a = scan_config(str(after))

    score_b = calculate(static_b.warnings, build_result_b, security_result_b)
    score_a = calculate(static_a.warnings, build_result_a, security_result_a)

    if format == "json":
        typer.echo(
            json_report.compare_to_json(
                static_b,
                score_b,
                build_result_b,
                security_result_b,
                static_a,
                score_a,
                build_result_a,
                security_result_a,
            )
        )
    else:
        console_reporter.print_compare(
            static_b,
            score_b,
            build_result_b,
            security_result_b,
            static_a,
            score_a,
            build_result_a,
            security_result_a,
            str(before),
            str(after),
        )

    if build_result_a is not None and not build_result_a.success:
        sys.exit(2)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
