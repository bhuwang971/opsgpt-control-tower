from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.cycle7.workflow import run_decision_workflow, write_workflow_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 7 decision workflow")
    parser.add_argument("--objective", default=None)
    parser.add_argument("--artifact-dir", default="artifacts/cycle7")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_cycle7(objective=args.objective, artifact_dir=Path(args.artifact_dir))
    print(json.dumps(result, indent=2))


def run_cycle7(*, objective: str | None, artifact_dir: Path) -> dict[str, Any]:
    result = run_decision_workflow(objective)
    result["artifacts"] = write_workflow_artifacts(result, artifact_dir)
    return result


if __name__ == "__main__":
    main()
