from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.control_tower import repo_root
from app.cycle6.assistant import answer_question

SAFE_REFUSAL = "I do not have enough grounded evidence in the local corpus to answer that safely."


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    question: str
    expected_mode: str
    expected_source: str | None = None
    expected_refusal: bool = False


def evaluation_cases() -> list[EvalCase]:
    return [
        EvalCase(
            case_id="retrieval_cycle6",
            question="What does the implementation cadence plan say about Cycle 6?",
            expected_mode="retrieval",
            expected_source="docs/implementation-cadence-plan.md",
        ),
        EvalCase(
            case_id="retrieval_architecture",
            question="What does the architecture doc say about Prometheus and Grafana?",
            expected_mode="retrieval",
            expected_source="docs/architecture.md",
        ),
        EvalCase(
            case_id="sql_daily_latest",
            question="Show the latest daily reliability and on-time trend",
            expected_mode="sql",
        ),
        EvalCase(
            case_id="sql_carrier_delay",
            question="Show the worst carrier delay",
            expected_mode="sql",
        ),
        EvalCase(
            case_id="retrieval_unknown",
            question="What is the exact FAA policy bulletin number mentioned in the local docs?",
            expected_mode="retrieval",
            expected_refusal=True,
        ),
    ]


def run_rag_evaluation() -> dict[str, Any]:
    cases = evaluation_cases()
    results = [_evaluate_case(case) for case in cases]
    retrieval_cases = [item for item in results if item["expected_mode"] == "retrieval"]
    refusal_cases = [item for item in results if item["expected_refusal"]]
    sql_cases = [item for item in results if item["expected_mode"] == "sql"]

    summary = {
        "total_cases": len(results),
        "mode_accuracy": _mean([1.0 if item["mode_match"] else 0.0 for item in results]),
        "retrieval_source_hit_rate": _mean(
            [1.0 if item["source_match"] else 0.0 for item in retrieval_cases]
        ),
        "citation_coverage": _mean(
            [1.0 if item["citation_count"] > 0 else 0.0 for item in retrieval_cases]
        ),
        "refusal_precision": _mean(
            [1.0 if item["refusal_match"] else 0.0 for item in refusal_cases]
        ),
        "hallucination_rate_proxy": _mean(
            [1.0 if item["hallucination_flag"] else 0.0 for item in retrieval_cases]
        ),
        "sql_success_rate": _mean(
            [1.0 if item["sql_rows_returned"] else 0.0 for item in sql_cases]
        ),
    }
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "corpus_paths": [
            "README.md",
            "docs/architecture.md",
            "docs/implementation-cadence-plan.md",
            "docs/runbook.md",
            "warehouse/glossary.md",
        ],
        "summary": summary,
        "cases": results,
    }


def write_rag_evaluation(result: dict[str, Any], artifact_dir: Path) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = artifact_dir / f"cycle6_rag_eval_{timestamp}.json"
    md_path = artifact_dir / f"cycle6_rag_eval_{timestamp}.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md_path.write_text(_markdown_report(result), encoding="utf-8")
    return {"json_report": str(json_path), "markdown_report": str(md_path)}


def _evaluate_case(case: EvalCase) -> dict[str, Any]:
    response = answer_question(case.question)
    citation_sources = [item["source"] for item in response.citations]
    answer_is_refusal = response.answer.strip() == SAFE_REFUSAL
    mode_match = response.mode == case.expected_mode
    source_match = (
        True if case.expected_source is None else case.expected_source in citation_sources
    )
    refusal_match = answer_is_refusal if case.expected_refusal else not answer_is_refusal
    hallucination_flag = (
        response.mode == "retrieval"
        and not case.expected_refusal
        and (not response.citations or not source_match)
    ) or (case.expected_refusal and not answer_is_refusal)
    return {
        **asdict(case),
        "observed_mode": response.mode,
        "mode_match": mode_match,
        "citation_sources": citation_sources,
        "citation_count": len(response.citations),
        "source_match": source_match,
        "answer_preview": response.answer[:200],
        "answer_is_refusal": answer_is_refusal,
        "refusal_match": refusal_match,
        "hallucination_flag": hallucination_flag,
        "sql_rows_returned": bool(response.sql and response.sql["rows"]),
        "passed": mode_match and source_match and refusal_match,
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    case_lines = [
        (
            f"- `{case['case_id']}`: mode={case['observed_mode']}, "
            f"passed={case['passed']}, citations={case['citation_count']}, "
            f"hallucination_flag={case['hallucination_flag']}"
        )
        for case in result["cases"]
    ]
    return "\n".join(
        [
            "# Cycle 6 RAG Evaluation",
            "",
            "## Summary",
            f"- total cases: {summary['total_cases']}",
            f"- mode accuracy: {summary['mode_accuracy']:.3f}",
            f"- retrieval source hit rate: {summary['retrieval_source_hit_rate']:.3f}",
            f"- citation coverage: {summary['citation_coverage']:.3f}",
            f"- refusal precision: {summary['refusal_precision']:.3f}",
            f"- hallucination rate proxy: {summary['hallucination_rate_proxy']:.3f}",
            f"- sql success rate: {summary['sql_success_rate']:.3f}",
            "",
            "## Cases",
            *case_lines,
            "",
            "## Notes",
            "- This eval pack is deterministic and local-corpus-backed.",
            "- Hallucination is approximated through refusal failures and missing expected sources.",
            "- Next step would be adding prompt-injection and adversarial red-team sets.",
        ]
    ) + "\n"


def default_eval_artifact_dir() -> Path:
    return repo_root() / "backend" / "artifacts" / "cycle6"


def _mean(values: list[float]) -> float:
    return 0.0 if not values else sum(values) / len(values)
