from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.cycle8.observability import provision_observability_assets
from app.cycle8.replay import replay_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 8 replay and observability")
    parser.add_argument("--artifact-dir", default="artifacts/cycle8")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_cycle8(Path(args.artifact_dir))
    print(json.dumps(result, indent=2))


def run_cycle8(artifact_dir: Path) -> dict[str, Any]:
    observability = provision_observability_assets()
    replay = replay_events()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    status_path = artifact_dir / "cycle8_live_status.json"
    status_path.write_text(json.dumps(replay, indent=2), encoding="utf-8")
    return {
        "observability": observability,
        "replay": replay,
        "status_json": str(status_path),
    }


if __name__ == "__main__":
    main()
