"""
Monitoring Engine Orchestrator
Coordinates continuous collection across CPU, Memory, Disk, Network,
and Process collectors, feeds the alert engine, maintains historical trend
buffers, and triggers periodic JSON reports and visual charts.
"""

import time
import signal
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

from monitor.cpu import get_cpu_metrics
from monitor.memory import get_memory_metrics
from monitor.disk import get_disk_metrics
from monitor.network import get_network_metrics
from monitor.process import get_process_summary
from monitor.alerts import AlertManager
from monitor.reporter import (
    get_system_metadata,
    generate_json_report,
    generate_visual_chart,
    format_text_summary
)


class MonitoringEngine:
    """Central engine running periodic metric collection, alerting, and reporting."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.general_cfg = config.get("general", {})
        self.sampling_interval = self.general_cfg.get("sampling_interval_seconds", 3)
        self.report_interval = self.general_cfg.get("report_interval_seconds", 30)
        self.history_size = self.general_cfg.get("history_retention_points", 60)
        self.top_proc_count = self.general_cfg.get("top_process_count", 8)
        self.reports_dir = config.get("paths", {}).get("reports_dir", "reports")

        self.alert_manager = AlertManager(config)
        self.history: deque = deque(maxlen=self.history_size)
        self.running = False
        self.last_report_time = 0.0

    def collect_snapshot(self) -> Dict[str, Any]:
        """Collect an instantaneous snapshot of all system metrics."""
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata = get_system_metadata()
        cpu = get_cpu_metrics(sample_interval=None)
        memory = get_memory_metrics()
        disk = get_disk_metrics()
        network = get_network_metrics()
        processes = get_process_summary(top_n=self.top_proc_count)

        return {
            "timestamp": now_iso,
            "metadata": metadata,
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "network": network,
            "processes": processes
        }

    def _record_history_point(self, snapshot: Dict[str, Any]):
        """Record condensed time-series point for charting."""
        cpu_pct = snapshot.get("cpu", {}).get("total_percent", 0.0)
        ram_pct = snapshot.get("memory", {}).get("ram", {}).get("percent", 0.0)
        net_overall = snapshot.get("network", {}).get("overall", {})
        net_up_kb = net_overall.get("upload_speed_bytes_sec", 0.0) / 1024.0
        net_down_kb = net_overall.get("download_speed_bytes_sec", 0.0) / 1024.0

        self.history.append({
            "timestamp": snapshot.get("timestamp"),
            "cpu_percent": cpu_pct,
            "ram_percent": ram_pct,
            "net_sent_kb": round(net_up_kb, 1),
            "net_recv_kb": round(net_down_kb, 1)
        })

    def run_once(self) -> (Dict[str, Any], List[Dict[str, Any]]):
        """
        Execute a single monitoring pass:
        Collects metrics, evaluates thresholds, appends to history.
        """
        snapshot = self.collect_snapshot()
        active_alerts = self.alert_manager.evaluate(snapshot)
        self._record_history_point(snapshot)
        return snapshot, active_alerts

    def maybe_generate_periodic_reports(self, snapshot: Dict[str, Any], active_alerts: List[Dict[str, Any]], force: bool = False):
        """Check if periodic report interval has elapsed and generate reports if so."""
        now = time.time()
        if force or (now - self.last_report_time >= self.report_interval):
            self.last_report_time = now
            gen_cfg = self.config.get("reporting", {})

            json_path = None
            chart_path = None

            if gen_cfg.get("generate_json", True):
                json_path = generate_json_report(
                    snapshot=snapshot,
                    history=list(self.history),
                    active_alerts=active_alerts,
                    output_dir=self.reports_dir
                )

            if gen_cfg.get("generate_charts", True):
                chart_path = generate_visual_chart(
                    history=list(self.history),
                    current_snapshot=snapshot,
                    thresholds=self.config.get("thresholds", {}),
                    output_dir=self.reports_dir
                )

            self.alert_manager.logger.info(
                f"[REPORT GENERATED] JSON: {json_path or 'N/A'}, Chart: {chart_path or 'N/A'}"
            )
            return json_path, chart_path

        return None, None

    def start(self, duration_seconds: Optional[int] = None, cycle_callback: Optional[Callable] = None):
        """
        Start continuous monitoring loop.
        
        :param duration_seconds: Optional max runtime in seconds before exiting.
        :param cycle_callback: Optional callback invoked on every poll cycle with (snapshot, alerts).
        """
        self.running = True
        self.last_report_time = time.time()

        # Handle signals gracefully
        def _stop_handler(sig, frame):
            print("\nShutting down system monitor gracefully...")
            self.running = False

        try:
            signal.signal(signal.SIGINT, _stop_handler)
            signal.signal(signal.SIGTERM, _stop_handler)
        except (ValueError, AttributeError):
            pass

        start_time = time.time()
        print(f"System Monitor started (Sampling every {self.sampling_interval}s, Reports every {self.report_interval}s)")

        try:
            while self.running:
                loop_start = time.time()
                snapshot, active_alerts = self.run_once()

                # Generate reports if schedule hit
                self.maybe_generate_periodic_reports(snapshot, active_alerts)

                if cycle_callback:
                    cycle_callback(snapshot, active_alerts)

                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    print(f"Target duration of {duration_seconds}s reached. Stopping monitor.")
                    break

                elapsed = time.time() - loop_start
                sleep_time = max(0.1, self.sampling_interval - elapsed)
                time.sleep(sleep_time)

        finally:
            self.running = False
            # Generate final summary report upon shutdown
            if self.history:
                last_snap = self.collect_snapshot()
                self.maybe_generate_periodic_reports(last_snap, [], force=True)
            print("System Monitor stopped.")
