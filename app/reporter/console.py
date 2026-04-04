from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from app.analyzer.static_analyzer import StaticAnalysisResult
from app.analyzer.build_analyzer import BuildResult
from app.scorer.calculator import ScoreResult

console = Console()

_SEVERITY_COLOR = {"high": "red", "medium": "yellow"}
_GRADE_COLOR = {"Good": "green", "Warning": "yellow", "Risky": "red"}


def _format_base_images(base_images: list[str], fallback: str) -> str:
    if not base_images:
        return fallback
    if len(base_images) == 1:
        return base_images[0]
    return " / ".join(
        f"stage{index}: {image}"
        for index, image in enumerate(base_images, start=1)
    )


def print_compare(
    static_b: StaticAnalysisResult,
    score_b: ScoreResult,
    build_result_b: BuildResult | None,
    static_a: StaticAnalysisResult,
    score_a: ScoreResult,
    build_result_a: BuildResult | None,
    before_path: str,
    after_path: str,
) -> None:
    console.rule("[bold yellow]◀  BEFORE[/bold yellow]")
    print_report(static_b, score_b, build_result_b, before_path)

    console.rule("[bold green]▶  AFTER[/bold green]")
    print_report(static_a, score_a, build_result_a, after_path)

    # ── 비교 요약 ────────────────────────────────────────────────
    diff = score_a.score - score_b.score
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    diff_color = "green" if diff > 0 else ("red" if diff < 0 else "white")
    grade_b_color = _GRADE_COLOR.get(score_b.grade, "white")
    grade_a_color = _GRADE_COLOR.get(score_a.grade, "white")

    summary = (
        f"[bold]BEFORE[/bold] [{grade_b_color}]{score_b.score}점  {score_b.grade}[/{grade_b_color}]"
        f"  →  "
        f"[bold]AFTER[/bold] [{grade_a_color}]{score_a.score}점  {score_a.grade}[/{grade_a_color}]"
        f"  |  [{diff_color}]{diff_str}점[/{diff_color}]"
    )
    console.rule("[bold]비교 결과[/bold]")
    console.print(Panel(summary, expand=False))


def print_report(
    static: StaticAnalysisResult,
    score_result: ScoreResult,
    build_result: BuildResult | None,
    file_path: str,
) -> None:
    # ── 헤더 ────────────────────────────────────────────────────
    base_images = _format_base_images(static.base_images, static.base_image)
    header = f"[bold]파일:[/bold] {file_path}\n[bold]베이스 이미지:[/bold] {base_images}"
    console.print(Panel(header, title="[bold cyan]Docktor Analysis[/bold cyan]", expand=False))

    # ── 경고 없음 ────────────────────────────────────────────────
    if not static.warnings:
        console.print("\n[green]✔ 감지된 문제가 없습니다.[/green]\n")
    else:
        # ── 경고 테이블 ──────────────────────────────────────────
        table = Table(box=box.ROUNDED, show_lines=True, expand=False)
        table.add_column("심각도", style="bold", width=8)
        table.add_column("줄", width=5)
        table.add_column("메시지")
        table.add_column("감점", width=6, justify="right")

        for w in static.warnings:
            color = _SEVERITY_COLOR.get(w.severity, "white")
            table.add_row(
                f"[{color}]{w.severity.upper()}[/{color}]",
                str(w.line) if w.line else "-",
                w.message,
                f"[{color}]-{w.deduction}[/{color}]",
            )

        console.print(table)

        # ── 경고 상세 ────────────────────────────────────────────
        detail_lines = []
        for i, w in enumerate(static.warnings):
            color = _SEVERITY_COLOR.get(w.severity, "white")
            if i > 0:
                detail_lines.append("")
            detail_lines.append(f"[{color}][bold]{w.severity.upper()} — {w.message}[/bold][/{color}]")
            detail_lines.append(f"  [bold]규칙:[/bold] {w.rule}")
            detail_lines.append(f"  [bold]왜?:[/bold] {w.why}")
            detail_lines.append(f"  [bold]해결:[/bold] {w.fix}")
        console.print(
            Panel("\n".join(detail_lines), title="[bold cyan]📋 경고 상세[/bold cyan]", expand=True)
        )

    # ── 빌드 결과 ────────────────────────────────────────────────
    if build_result is not None:
        if build_result.success:
            time_str = f"{build_result.build_time_seconds}s" if build_result.build_time_seconds is not None else "-"
            size_str = f"{build_result.image_size_mb}MB" if build_result.image_size_mb is not None else "-"
            image_id_str = (
                build_result.image_id.removeprefix("sha256:")
                if build_result.image_id
                else "-"
            )
            build_text = (
                f"[bold]빌드:[/bold] [green]성공[/green]  |  "
                f"[bold]소요시간:[/bold] {time_str}  |  "
                f"[bold]이미지 크기:[/bold] {size_str}\n"
                f"[bold]Image ID:[/bold] {image_id_str}"
            )
            if build_result.tag:
                build_text += f"\n[bold]태그:[/bold] {build_result.tag}"
            if build_result.cache_summary:
                build_text += f"\n[bold]캐시 분석:[/bold] {build_result.cache_summary}"
        else:
            build_text = f"[bold]빌드:[/bold] [red]실패[/red]\n{build_result.error_message or ''}"
        console.print(Panel(build_text, title="[bold cyan]🔨 빌드 결과[/bold cyan]", expand=True))

    # ── 최종 점수 ────────────────────────────────────────────────
    grade_color = _GRADE_COLOR.get(score_result.grade, "white")
    score_text = Text(justify="center")
    score_text.append(f"{score_result.score}점", style=f"bold {grade_color} on default")
    score_text.append("  |  ")
    score_text.append(score_result.grade, style=f"bold {grade_color}")
    console.print(Panel(score_text, title="[bold]최종 점수[/bold]", expand=False))
