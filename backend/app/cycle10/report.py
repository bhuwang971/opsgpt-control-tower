from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def write_cycle10_report(result: dict[str, Any], artifact_dir: Path) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    markdown_path = artifact_dir / f"cycle10_portfolio_{timestamp}.md"
    json_path = artifact_dir / f"cycle10_portfolio_{timestamp}.json"
    markdown_path.write_text(_markdown_report(result), encoding="utf-8")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {"markdown_report": str(markdown_path), "json_report": str(json_path)}


def _markdown_report(result: dict[str, Any]) -> str:
    policies = "\n".join(
        [
            (
                f"- `{item['policy_name']}`: IPS={item['estimated_reward_ips']:.4f}, "
                f"DM={item['estimated_reward_dm']:.4f}, "
                f"DR={item['estimated_reward_dr']:.4f}, "
                f"match_rate={item['match_rate']:.4f}"
            )
            for item in result["ope"]["policies"]
        ]
    )
    notes = "\n".join([f"- {item}" for item in result["ope"]["showcase_notes"]])
    return "\n".join(
        [
            "# Cycle 10 Portfolio Report",
            "",
            "## Offline Policy Evaluation",
            policies,
            "",
            "## Champion",
            f"- policy: {result['ope']['champion_policy']['policy_name']}",
            f"- dr estimate: {result['ope']['champion_policy']['estimated_reward_dr']:.4f}",
            "",
            "## Demo Assets",
            f"- architecture doc: {result['demo_assets']['architecture_doc']}",
            f"- demo script: {result['demo_assets']['demo_script']}",
            "",
            "## Notes",
            notes,
        ]
    )
