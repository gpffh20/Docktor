from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Instruction:
    line: int       # 원본 파일 시작 줄 번호
    name: str       # 대문자 정규화 ("FROM", "USER", "COPY" ...)
    value: str      # 명령어 이후 전체 인자


@dataclass
class Warning:
    rule: str           # "latest_tag" 등
    severity: str       # "high" | "medium"
    line: int | None    # 특정 줄 기반이면 int, 파일 전체 문제면 None
    message: str
    why: str
    fix: str
    deduction: int      # 양수만 사용 (예: 15, 20, 10)


@dataclass
class StaticAnalysisResult:
    warnings: list[Warning]
    base_image: str     # FROM 라인에서 추출


class BaseRule(ABC):
    @abstractmethod
    def feed(self, instruction: Instruction) -> None:
        """명령어를 한 줄씩 받아 내부 상태를 갱신합니다."""
        raise NotImplementedError

    @abstractmethod
    def result(self) -> list[Warning]:
        """전체 순회 후 최종 경고 리스트를 반환합니다. 위반 없으면 [] 반환."""
        raise NotImplementedError