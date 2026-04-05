import json
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")


@dataclass
class SecuritySummary:
    scanner: str
    target: str
    total_findings: int
    severity_counts: dict[str, int]


@dataclass
class SecurityScanResult:
    success: bool
    mode: str
    target: str
    summary: SecuritySummary | None
    error_message: str | None


def _empty_counts() -> dict[str, int]:
    return {severity: 0 for severity in _SEVERITIES}


def _install_guide() -> str:
    system = platform.system().lower()

    if system == "windows":
        return (
            "Trivy가 설치되어 있지 않습니다.\n"
            "Windows에서는 아래 방법 중 하나로 설치하세요.\n"
            "- winget install AquaSecurity.Trivy\n"
            "- choco install trivy\n"
            "설치 후 `trivy --version`으로 확인하세요.\n"
            "공식 문서: https://trivy.dev/docs/latest/getting-started/installation/"
        )

    if system == "darwin":
        return (
            "Trivy가 설치되어 있지 않습니다.\n"
            "macOS에서는 `brew install trivy`로 설치할 수 있습니다.\n"
            "설치 후 `trivy --version`으로 확인하세요.\n"
            "공식 문서: https://trivy.dev/docs/latest/getting-started/installation/"
        )

    return (
        "Trivy가 설치되어 있지 않습니다.\n"
        "Linux에서는 배포판에 맞는 패키지 매니저 또는 바이너리 설치를 사용하세요.\n"
        "설치 후 `trivy --version`으로 확인하세요.\n"
        "공식 문서: https://trivy.dev/docs/latest/getting-started/installation/"
    )


def _merge_count(
    counts: dict[str, int],
    severity: str | None,
    amount: int = 1,
) -> None:
    key = (severity or "UNKNOWN").upper()
    if key not in counts:
        key = "UNKNOWN"
    counts[key] += amount


def _parse_results(results: list[dict]) -> tuple[int, dict[str, int]]:
    total = 0
    counts = _empty_counts()

    for result in results:
        for vulnerability in result.get("Vulnerabilities") or []:
            total += 1
            _merge_count(counts, vulnerability.get("Severity"))

        misconfigurations = result.get("Misconfigurations") or []
        if misconfigurations:
            for misconfiguration in misconfigurations:
                status = (misconfiguration.get("Status") or "").upper()
                if status and status not in {"FAIL", "FAILED"}:
                    continue
                total += 1
                _merge_count(counts, misconfiguration.get("Severity"))
        else:
            misconfig_summary = result.get("MisconfSummary") or {}
            misconfig_total = (
                misconfig_summary.get("CriticalCount", 0)
                + misconfig_summary.get("HighCount", 0)
                + misconfig_summary.get("MediumCount", 0)
                + misconfig_summary.get("LowCount", 0)
            )
            if misconfig_total:
                total += misconfig_total
                _merge_count(counts, "CRITICAL", misconfig_summary.get("CriticalCount", 0))
                _merge_count(counts, "HIGH", misconfig_summary.get("HighCount", 0))
                _merge_count(counts, "MEDIUM", misconfig_summary.get("MediumCount", 0))
                _merge_count(counts, "LOW", misconfig_summary.get("LowCount", 0))

        for secret in result.get("Secrets") or []:
            total += 1
            _merge_count(counts, secret.get("Severity"))

    return total, counts


def _scan(command: list[str], mode: str, target: str) -> SecurityScanResult:
    if shutil.which("trivy") is None:
        return SecurityScanResult(
            success=False,
            mode=mode,
            target=target,
            summary=None,
            error_message=_install_guide(),
        )

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        error_message = result.stderr.strip() or result.stdout.strip() or "Trivy 실행에 실패했습니다."
        return SecurityScanResult(
            success=False,
            mode=mode,
            target=target,
            summary=None,
            error_message=error_message,
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return SecurityScanResult(
            success=False,
            mode=mode,
            target=target,
            summary=None,
            error_message="Trivy JSON 결과를 파싱하지 못했습니다.",
        )

    total, counts = _parse_results(payload.get("Results") or [])
    summary = SecuritySummary(
        scanner=mode,
        target=target,
        total_findings=total,
        severity_counts=counts,
    )
    return SecurityScanResult(
        success=True,
        mode=mode,
        target=target,
        summary=summary,
        error_message=None,
    )


def scan_config(file_path: str) -> SecurityScanResult:
    path = Path(file_path)
    scan_target = str(path.parent if path.is_file() else path)
    command = [
        "trivy",
        "config",
        "--format",
        "json",
        "--quiet",
        "--misconfig-scanners",
        "dockerfile",
        scan_target,
    ]
    return _scan(command, mode="config", target=file_path)


def scan_image(image_ref: str) -> SecurityScanResult:
    command = [
        "trivy",
        "image",
        "--format",
        "json",
        "--quiet",
        "--scanners",
        "vuln,secret",
        "--image-config-scanners",
        "misconfig,secret",
        image_ref,
    ]
    return _scan(command, mode="image", target=image_ref)
