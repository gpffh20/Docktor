import json
from dataclasses import asdict

from app.analyzer.static_analyzer import StaticAnalysisResult
from app.analyzer.build_analyzer import BuildResult
from app.scorer.calculator import ScoreResult


def compare_to_json(
    static_b: StaticAnalysisResult,
    score_b: ScoreResult,
    build_result_b: BuildResult | None,
    static_a: StaticAnalysisResult,
    score_a: ScoreResult,
    build_result_a: BuildResult | None,
) -> str:
    data = {
        "before": {
            "score": score_b.score,
            "grade": score_b.grade,
            "base_image": static_b.base_image,
            "base_images": static_b.base_images,
            "warnings": [asdict(w) for w in static_b.warnings],
            "build": asdict(build_result_b) if build_result_b is not None else None,
        },
        "after": {
            "score": score_a.score,
            "grade": score_a.grade,
            "base_image": static_a.base_image,
            "base_images": static_a.base_images,
            "warnings": [asdict(w) for w in static_a.warnings],
            "build": asdict(build_result_a) if build_result_a is not None else None,
        },
        "diff": score_a.score - score_b.score,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_json(
    static: StaticAnalysisResult,
    score_result: ScoreResult,
    build_result: BuildResult | None,
) -> str:
    data = {
        "score": score_result.score,
        "grade": score_result.grade,
        "base_image": static.base_image,
        "base_images": static.base_images,
        "warnings": [asdict(w) for w in static.warnings],
        "build": asdict(build_result) if build_result is not None else None,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
