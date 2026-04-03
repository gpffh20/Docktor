from dataclasses import dataclass

from app.analyzer.rules.base import Warning
from app.analyzer.build_analyzer import BuildResult


@dataclass
class ScoreResult:
    score: int
    grade: str  # "Good" | "Warning" | "Risky"


def _image_size_deduction(image_size_mb: float) -> int:
    if image_size_mb <= 200:
        return 0
    elif image_size_mb <= 500:
        return 5
    elif image_size_mb <= 1024:
        return 10
    else:
        return 20


def calculate(warnings: list[Warning], build_result: BuildResult | None) -> ScoreResult:
    static_deduction = sum(w.deduction for w in warnings)

    build_deduction = 0
    if build_result is not None and build_result.success and build_result.image_size_mb is not None:
        build_deduction = _image_size_deduction(build_result.image_size_mb)

    score = max(0, 100 - static_deduction - build_deduction)

    if build_result is not None and not build_result.success:
        grade = "Risky"
    elif score >= 80:
        grade = "Good"
    elif score >= 50:
        grade = "Warning"
    else:
        grade = "Risky"

    return ScoreResult(score=score, grade=grade)
