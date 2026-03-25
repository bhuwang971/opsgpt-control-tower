from __future__ import annotations

import json

from app.control_tower import repo_root


def provision_observability_assets() -> dict[str, str]:
    grafana_dir = repo_root() / "infra" / "grafana" / "provisioning" / "dashboards"
    grafana_dir.mkdir(parents=True, exist_ok=True)
    dashboards_yml = grafana_dir.parent / "dashboards.yml"
    dashboard_json = grafana_dir / "control_tower_live_ops.json"
    alert_rules = repo_root() / "infra" / "prometheus" / "alert_rules.yml"

    dashboards_yml.write_text(
        """
apiVersion: 1
providers:
  - name: OpsGPT Dashboards
    folder: OpsGPT
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
""".strip()
        + "\n",
        encoding="utf-8",
    )
    dashboard_json.write_text(json.dumps(_dashboard_payload(), indent=2), encoding="utf-8")
    alert_rules.write_text(
        """
groups:
  - name: opsgpt_control_tower
    rules:
      - alert: OpsGPTLiveOnTimeRateLow
        expr: opsgpt_live_on_time_rate < 0.45
        for: 1m
        labels:
          severity: high
        annotations:
          summary: Live on-time rate is below the watch threshold.

      - alert: OpsGPTActiveAlertsPresent
        expr: opsgpt_active_alerts > 0
        for: 1m
        labels:
          severity: medium
        annotations:
          summary: One or more replay-driven control tower alerts are active.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return {
        "grafana_dashboards_yml": str(dashboards_yml),
        "grafana_dashboard_json": str(dashboard_json),
        "prometheus_alert_rules": str(alert_rules),
    }


def _dashboard_payload() -> dict[str, object]:
    return {
        "title": "OpsGPT Live Ops",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "10s",
        "panels": [
            {
                "type": "stat",
                "title": "Replay Events Processed",
                "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
                "targets": [{"expr": "opsgpt_replay_events_total"}],
            },
            {
                "type": "stat",
                "title": "Active Alerts",
                "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0},
                "targets": [{"expr": "opsgpt_active_alerts"}],
            },
            {
                "type": "stat",
                "title": "Live On-Time Rate",
                "gridPos": {"h": 6, "w": 8, "x": 16, "y": 0},
                "targets": [{"expr": "opsgpt_live_on_time_rate"}],
            },
        ],
    }
