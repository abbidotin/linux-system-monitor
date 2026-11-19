#!/usr/bin/env python3
"""
System Health Monitor - Main CLI Application
Provides cross-platform commands for interactive snapshots, real-time live terminal monitoring,
and continuous daemon service with alerting and periodic report generation on Linux and Windows.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor.engine import MonitoringEngine
from monitor.reporter import format_text_summary


DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.json")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file or return defaults."""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not parse config at {config_path}: {e}. Using defaults.")

    return {
        "general": {
            "sampling_interval_seconds": 3,
            "report_interval_seconds": 30,
            "history_retention_points": 60,
            "top_process_count": 8
        },
        "thresholds": {
            "cpu_percent": {"warning": 75.0, "critical": 90.0},
            "ram_percent": {"warning": 80.0, "critical": 92.0},
            "swap_percent": {"warning": 60.0, "critical": 85.0},
            "disk_percent": {"warning": 85.0, "critical": 95.0}
        },
        "alerts": {
            "cooldown_seconds": 60,
            "log_alerts_to_console": True
        },
        "paths": {
            "log_file": "logs/monitor.log",
            "reports_dir": "reports"
        },
        "reporting": {
            "generate_json": True,
            "generate_charts": True
        }
    }


def handle_snapshot(engine: MonitoringEngine):
    """Execute a single snapshot pass, print summary, and generate snapshot reports."""
    print("Collecting system metrics snapshot...\n")
    snapshot, active_alerts = engine.run_once()

    # Print formatted text summary
    print(format_text_summary(snapshot, active_alerts))

    # Generate snapshot reports
    json_path, chart_path = engine.maybe_generate_periodic_reports(snapshot, active_alerts, force=True)
    print("\nReports Generated:")
    if json_path:
        print(f" - JSON Report: {json_path}")
    if chart_path:
        print(f" - Visual Chart: {chart_path}")


def handle_watch(engine: MonitoringEngine, duration: int = None):
    """Run an interactive live updating terminal dashboard."""
    def _watch_callback(snapshot: Dict[str, Any], active_alerts: list):
        # Clear terminal screen (cross-platform)
        os.system("cls" if os.name == "nt" else "clear")
        print(format_text_summary(snapshot, active_alerts))
        print(f"\n[Watch Mode] Refreshing every {engine.sampling_interval}s. Press Ctrl+C to exit.")

    try:
        engine.start(duration_seconds=duration, cycle_callback=_watch_callback)
    except KeyboardInterrupt:
        pass


def handle_daemon(engine: MonitoringEngine, duration: int = None):
    """Run continuous background monitor generating alerts and periodic reports."""
    print(f"Starting System Monitor Daemon...")
    print(f" - Polling interval: {engine.sampling_interval}s")
    print(f" - Reporting interval: {engine.report_interval}s")
    print(f" - Logs written to: {engine.config.get('paths', {}).get('log_file')}")
    print(f" - Reports saved to: {engine.reports_dir}/")
    print("Press Ctrl+C to stop daemon.")

    def _daemon_callback(snapshot: Dict[str, Any], active_alerts: list):
        # In daemon mode, we print concise heartbeats
        cpu_pct = snapshot.get("cpu", {}).get("total_percent", 0.0)
        ram_pct = snapshot.get("memory", {}).get("ram", {}).get("percent", 0.0)
        alert_str = f" [! {len(active_alerts)} Alerts]" if active_alerts else " [OK]"
        print(f"[{snapshot.get('timestamp')}] CPU: {cpu_pct:>5.1f}% | RAM: {ram_pct:>5.1f}%{alert_str}")

    try:
        engine.start(duration_seconds=duration, cycle_callback=_daemon_callback)
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="System Health Monitor - Cross-Platform CPU, RAM, Disk, Process, Network Monitoring & Alerts (Linux & Windows)"
    )
    parser.add_argument(
        "mode",
        choices=["snapshot", "watch", "daemon"],
        nargs="?",
        default="snapshot",
        help="Operating mode: 'snapshot' (instant diagnostic), 'watch' (live dashboard), or 'daemon' (background alerting service)"
    )
    parser.add_argument(
        "-c", "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to configuration JSON file (default: config/config.json)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=None,
        help="Optional duration in seconds to run before exiting"
    )
    parser.add_argument(
        "--no-chart",
        action="store_true",
        help="Disable Matplotlib visual chart generation"
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Disable JSON report generation"
    )

    args = parser.parse_args()

    # Load and adjust config
    config = load_config(args.config)
    if args.no_chart:
        config.setdefault("reporting", {})["generate_charts"] = False
    if args.no_json:
        config.setdefault("reporting", {})["generate_json"] = False

    engine = MonitoringEngine(config)

    if args.mode == "snapshot":
        handle_snapshot(engine)
    elif args.mode == "watch":
        handle_watch(engine, duration=args.duration)
    elif args.mode == "daemon":
        handle_daemon(engine, duration=args.duration)


if __name__ == "__main__":
    main()
