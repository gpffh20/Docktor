from dataclasses import dataclass

from app.analyzer.rules.base import Warning
from app.analyzer.build_analyzer import BuildResult
from app.analyzer.security_analyzer import SecurityScanResult


@dataclass
class ScoreResult:
    score: int
    grade: str  # "Good" | "Warning" | "Risky"
    static_deduction: int
    build_deduction: int
    security_deduction: int


def _image_size_deduction(image_size_mb: float) -> int:
    if image_size_mb <= 200:
        return 0
    elif image_size_mb <= 500:
        return 5
    elif image_size_mb <= 1024:
        return 10
    else:
        return 20


def _security_deduction(security_result: SecurityScanResult | None) -> int:
    if security_result is None or not security_result.success or security_result.summary is None:
        return 0

    counts = security_result.summary.severity_counts
    deduction = (
        counts.get("CRITICAL", 0) * 15
        + counts.get("HIGH", 0) * 8
        + counts.get("MEDIUM", 0) * 3
    )
    return min(deduction, 40)


def calculate(
    warnings: list[Warning],
    build_result: BuildResult | None,
    security_result: SecurityScanResult | None = None,
) -> ScoreResult:
    static_deduction = sum(w.deduction for w in warnings)

    build_deduction = 0
    if build_result is not None and build_result.success and build_result.image_size_mb is not None:
        build_deduction = _image_size_deduction(build_result.image_size_mb)

    security_deduction = _security_deduction(security_result)
    score = max(0, 100 - static_deduction - build_deduction - security_deduction)

    if build_result is not None and not build_result.success:
        grade = "Risky"
    elif security_result is not None and not security_result.success:
        grade = "Warning"
    elif score >= 80:
        grade = "Good"
    elif score >= 50:
        grade = "Warning"
    else:
        grade = "Risky"

    return ScoreResult(
        score=score,
        grade=grade,
        static_deduction=static_deduction,
        build_deduction=build_deduction,
        security_deduction=security_deduction,
    )
