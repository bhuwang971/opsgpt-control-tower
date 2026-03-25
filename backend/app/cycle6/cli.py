from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.cycle6.eval import (
    default_eval_artifact_dir,
    run_rag_evaluation,
    write_rag_evaluation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 6 evaluation utilities")
    parser.add_argument("--artifact-dir", default=str(default_eval_artifact_dir()))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_eval(Path(args.artifact_dir))
    print(json.dumps(result, indent=2))


def run_eval(artifact_dir: Path) -> dict[str, Any]:
    evaluation = run_rag_evaluation()
    artifacts = write_rag_evaluation(evaluation, artifact_dir)
    return {"evaluation": evaluation, "artifacts": artifacts}


if __name__ == "__main__":
    main()
