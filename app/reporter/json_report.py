import json
from dataclasses import asdict

from app.analyzer.static_analyzer import StaticAnalysisResult
from app.analyzer.build_analyzer import BuildResult
from app.scorer.calculator import ScoreResult


def to_json(
    static: StaticAnalysisResult,
    score_result: ScoreResult,
    build_result: BuildResult | None,
) -> str:
    data = {
        "score": score_result.score,
        "grade": score_result.grade,
        "base_image": static.base_image,
        "warnings": [asdict(w) for w in static.warnings],
        "build": asdict(build_result) if build_result is not None else None,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
