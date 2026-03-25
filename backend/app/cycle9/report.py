from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def write_experiment_report(result: dict[str, Any], artifact_dir: Path) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    markdown_path = artifact_dir / f"cycle9_experiment_{timestamp}.md"
    json_path = artifact_dir / f"cycle9_experiment_{timestamp}.json"
    markdown_path.write_text(_markdown_report(result), encoding="utf-8")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {"markdown_report": str(markdown_path), "json_report": str(json_path)}


def _markdown_report(result: dict[str, Any]) -> str:
    primary = result["primary_metric_result"]
    guardrails = "\n".join(
        [
            (
                f"- `{item['metric']}`: control={item['control_value']:.4f}, "
                f"treatment={item['treatment_value']:.4f}, diff={item['difference']:.4f}, "
                f"status={item['status']}"
            )
            for item in result["guardrails"]
        ]
    )
    checks = "\n".join(
        [
            (
                f"- {item['checkpoint']}: lift={item['absolute_lift']:.4f}, "
                f"p={item['p_value']:.4f}, decision={item['decision']}"
            )
            for item in result["sequential_checks"]
        ]
    )
    segments = "\n".join(
        [
            (
                f"- {item['carrier_code']}: lift={item['absolute_lift']:.4f}, "
                f"sample={item['sample_size']}"
            )
            for item in result["segment_breakdown"][:5]
        ]
    )
    return "\n".join(
        [
            f"# Cycle 9 Experiment Report: {result['title']}",
            "",
            result["description"],
            "",
            "## Primary Metric",
            (
                f"- control rate: {primary['control_rate']:.4f}\n"
                f"- treatment rate: {primary['treatment_rate']:.4f}\n"
                f"- absolute lift: {primary['absolute_lift']:.4f}\n"
                f"- relative lift: {primary['relative_lift']:.4f}\n"
                f"- p-value: {primary['p_value']:.4f}\n"
                f"- significant: {primary['significant']}"
            ),
            "",
            "## Guardrails",
            guardrails,
            "",
            "## Sequential Checks",
            checks,
            "",
            "## Segment Breakdown",
            segments,
            "",
            "## Recommendation",
            f"- decision: {result['recommendation']['decision']}",
            f"- rationale: {result['recommendation']['rationale']}",
        ]
    )
