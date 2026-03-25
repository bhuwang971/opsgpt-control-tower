from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoEvaluation:
    score: int
    max_score: int
    rubric: list[dict[str, Any]]


def evaluate_memo(result: dict[str, Any]) -> MemoEvaluation:
    memo = result["memo_markdown"]
    evidence = result["evidence"]
    recommendations = result["recommendations"]
    rubric = [
        {
            "criterion": "has_diagnosis_section",
            "passed": "## Diagnosis" in memo,
        },
        {
            "criterion": "has_evidence_section",
            "passed": "## Evidence" in memo and len(evidence) >= 2,
        },
        {
            "criterion": "has_recommendations",
            "passed": "## Recommendations" in memo and len(recommendations) >= 2,
        },
        {
            "criterion": "has_tradeoffs",
            "passed": "## Trade-Offs" in memo,
        },
        {
            "criterion": "trace_is_stable",
            "passed": all(step["status"] == "completed" for step in result["trace"]),
        },
    ]
    score = sum(1 for item in rubric if item["passed"])
    return MemoEvaluation(score=score, max_score=len(rubric), rubric=rubric)
