from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.control_tower import control_tower_overview
from app.cycle6.assistant import answer_question
from app.cycle7.eval import evaluate_memo

DEFAULT_OBJECTIVE = "Stabilize network reliability and explain the current disruption pattern."


@dataclass(frozen=True)
class TraceStep:
    step: str
    status: str
    detail: str


def run_decision_workflow(objective: str | None = None) -> dict[str, Any]:
    trace: list[TraceStep] = []
    fallback_used = False

    overview = control_tower_overview()
    diagnosis = _diagnose(overview, objective)
    trace.append(
        TraceStep(
            step="diagnose",
            status="completed",
            detail=diagnosis["headline"],
        )
    )

    evidence: list[dict[str, Any]] = []
    prompts = [
        "Show the latest daily reliability and on-time trend",
        "Show the worst carrier delay",
        "What does the implementation cadence plan say about evidence-backed decision automation?",
    ]
    for prompt in prompts:
        try:
            answer = answer_question(prompt)
            evidence.append(
                {
                    "prompt": prompt,
                    "mode": answer.mode,
                    "answer": answer.answer,
                    "citations": answer.citations,
                    "sql": answer.sql,
                }
            )
        except Exception as exc:
            fallback_used = True
            evidence.append(
                {
                    "prompt": prompt,
                    "mode": "fallback",
                    "answer": f"Evidence call failed: {exc}",
                    "citations": [],
                    "sql": None,
                }
            )
    trace.append(
        TraceStep(
            step="gather_evidence",
            status="completed",
            detail=f"Collected {len(evidence)} evidence packets",
        )
    )

    recommendations = _recommend(overview, diagnosis)
    trace.append(
        TraceStep(
            step="recommend",
            status="completed",
            detail=f"Produced {len(recommendations)} recommendations",
        )
    )

    memo_markdown = _memo_markdown(
        objective=objective or DEFAULT_OBJECTIVE,
        diagnosis=diagnosis,
        evidence=evidence,
        recommendations=recommendations,
        fallback_used=fallback_used,
    )
    trace.append(
        TraceStep(
            step="memo",
            status="completed",
            detail="Generated markdown decision memo",
        )
    )

    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "objective": objective or DEFAULT_OBJECTIVE,
        "diagnosis": diagnosis,
        "evidence": evidence,
        "recommendations": recommendations,
        "memo_markdown": memo_markdown,
        "fallback_used": fallback_used,
        "trace": [asdict(step) for step in trace],
    }
    evaluation = evaluate_memo(result)
    result["evaluation"] = {
        "score": evaluation.score,
        "max_score": evaluation.max_score,
        "rubric": evaluation.rubric,
    }
    return result


def write_workflow_artifacts(result: dict[str, Any], artifact_dir: Path) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = artifact_dir / f"cycle7_decision_memo_{timestamp}.json"
    md_path = artifact_dir / f"cycle7_decision_memo_{timestamp}.md"
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    md_path.write_text(result["memo_markdown"], encoding="utf-8")
    return {"json_report": str(json_path), "markdown_report": str(md_path)}


def _diagnose(overview: dict[str, Any], objective: str | None) -> dict[str, Any]:
    latest_kpis = {item["id"]: item for item in overview["kpis"]}
    top_alert = overview["alerts"][0] if overview["alerts"] else None
    worst_carrier = overview["carrier_drilldown"][-1]
    headline = (
        top_alert["title"]
        if top_alert
        else "Operational attention required on reliability and delay volatility."
    )
    return {
        "headline": headline,
        "objective": objective or DEFAULT_OBJECTIVE,
        "latest_on_time_rate": latest_kpis["on_time_rate"]["display"],
        "latest_reliability_score": latest_kpis["reliability_score"]["display"],
        "worst_carrier": worst_carrier["carrier_code"],
        "worst_carrier_delay_minutes": worst_carrier["avg_arr_delay_minutes"],
    }


def _recommend(overview: dict[str, Any], diagnosis: dict[str, Any]) -> list[dict[str, str]]:
    forecast = overview["forecast"]["projected_on_time_rate"][0]
    worst_carrier = diagnosis["worst_carrier"]
    return [
        {
            "title": "Contain the highest-delay carrier segment",
            "detail": (
                f"Prioritize schedule and station review for {worst_carrier}, "
                "which currently carries the weakest carrier delay profile."
            ),
            "tradeoff": "May shift resources away from lower-risk network segments.",
        },
        {
            "title": "Stand up a short-horizon reliability watch",
            "detail": (
                f"Use the next projected day ({forecast['date']}) as the near-term checkpoint "
                f"with projected on-time rate {forecast['projected_on_time_rate']:.1%}."
            ),
            "tradeoff": (
                "Forecast is a baseline signal and should not be treated as "
                "a production forecast."
            ),
        },
        {
            "title": "Keep decisions tied to cited evidence and audited queries",
            "detail": (
                "Use the Cycle 6 assistant flow to preserve citations and SQL audit IDs "
                "when sharing operational narratives."
            ),
            "tradeoff": "Slightly slower than informal analysis, but safer and easier to review.",
        },
    ]


def _memo_markdown(
    *,
    objective: str,
    diagnosis: dict[str, Any],
    evidence: list[dict[str, Any]],
    recommendations: list[dict[str, str]],
    fallback_used: bool,
) -> str:
    lines = [
        "# Decision Memo",
        "",
        f"Objective: {objective}",
        "",
        "## Diagnosis",
        "",
        f"- Headline: {diagnosis['headline']}",
        f"- Latest on-time rate: {diagnosis['latest_on_time_rate']}",
        f"- Latest reliability score: {diagnosis['latest_reliability_score']}",
        (
            f"- Highest-risk carrier segment: {diagnosis['worst_carrier']} "
            f"({diagnosis['worst_carrier_delay_minutes']:.1f} avg delay minutes)"
        ),
        "",
        "## Evidence",
        "",
    ]
    for item in evidence:
        lines.append(f"- Prompt: {item['prompt']}")
        lines.append(f"  Mode: {item['mode']}")
        lines.append(f"  Answer: {item['answer']}")
        if item["citations"]:
            citation = item["citations"][0]
            lines.append(f"  Citation: {citation['source']} -> {citation['excerpt']}")
        if item["sql"]:
            lines.append(f"  Audit ID: {item['sql']['audit_id']}")
    lines.extend(["", "## Recommendations", ""])
    for item in recommendations:
        lines.append(f"- {item['title']}: {item['detail']}")
    lines.extend(["", "## Trade-Offs", ""])
    for item in recommendations:
        lines.append(f"- {item['tradeoff']}")
    lines.extend(["", "## Trace", ""])
    lines.append(f"- Fallback used: {'yes' if fallback_used else 'no'}")
    lines.append("- Workflow path: diagnose -> gather_evidence -> recommend -> memo")
    return "\n".join(lines) + "\n"
