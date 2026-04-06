import json
from dataclasses import asdict

from app.analyzer.static_analyzer import StaticAnalysisResult
from app.analyzer.build_analyzer import BuildResult
from app.analyzer.security_analyzer import SecurityScanResult
from app.scorer.calculator import ScoreResult


def compare_to_json(
    static_b: StaticAnalysisResult,
    score_b: ScoreResult,
    build_result_b: BuildResult | None,
    security_result_b: SecurityScanResult | None,
    static_a: StaticAnalysisResult,
    score_a: ScoreResult,
    build_result_a: BuildResult | None,
    security_result_a: SecurityScanResult | None,
) -> str:
    data = {
        "before": {
            "score": score_b.score,
            "grade": score_b.grade,
            "deductions": {
                "static": score_b.static_deduction,
                "build": score_b.build_deduction,
                "security": score_b.security_deduction,
            },
            "base_image": static_b.base_image,
            "base_images": static_b.base_images,
            "warnings": [asdict(w) for w in static_b.warnings],
            "build": asdict(build_result_b) if build_result_b is not None else None,
            "security": asdict(security_result_b) if security_result_b is not None else None,
        },
        "after": {
            "score": score_a.score,
            "grade": score_a.grade,
            "deductions": {
                "static": score_a.static_deduction,
                "build": score_a.build_deduction,
                "security": score_a.security_deduction,
            },
            "base_image": static_a.base_image,
            "base_images": static_a.base_images,
            "warnings": [asdict(w) for w in static_a.warnings],
            "build": asdict(build_result_a) if build_result_a is not None else None,
            "security": asdict(security_result_a) if security_result_a is not None else None,
        },
        "diff": score_a.score - score_b.score,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_json(
    static: StaticAnalysisResult,
    score_result: ScoreResult,
    build_result: BuildResult | None,
    security_result: SecurityScanResult | None,
) -> str:
    data = {
        "score": score_result.score,
        "grade": score_result.grade,
        "deductions": {
            "static": score_result.static_deduction,
            "build": score_result.build_deduction,
            "security": score_result.security_deduction,
        },
        "base_image": static.base_image,
        "base_images": static.base_images,
        "warnings": [asdict(w) for w in static.warnings],
        "build": asdict(build_result) if build_result is not None else None,
        "security": asdict(security_result) if security_result is not None else None,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
