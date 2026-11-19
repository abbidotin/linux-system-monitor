"""
Threshold-Based Alerting Engine
Monitors metrics against configurable warning and critical thresholds.
Includes alert cooldown, deduplication, auto-recovery notifications,
and structured logging to files and console.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class AlertManager:
    """Manages threshold evaluation, cooldown timers, and alert logging."""

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize AlertManager.
        
        :param config: Dictionary containing threshold and alert configurations.
        :param logger: Optional configured logging.Logger instance.
        """
        self.config = config
        self.thresholds = config.get("thresholds", {})
        self.cooldown_seconds = config.get("alerts", {}).get("cooldown_seconds", 60)
        self.log_to_console = config.get("alerts", {}).get("log_alerts_to_console", True)

        # Track alert history: key -> {"last_fired": timestamp, "severity": str, "value": float}
        self.alert_history: Dict[str, Dict[str, Any]] = {}

        # Set up logger
        self.logger = logger or self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure file and console logger for system alerts."""
        logger = logging.getLogger("SystemMonitor.Alerts")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            log_path = self.config.get("paths", {}).get("log_file", "logs/monitor.log")
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [SystemMonitor] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # File handler
            try:
                fh = logging.FileHandler(log_path, encoding="utf-8")
                fh.setLevel(logging.INFO)
                fh.setFormatter(formatter)
                logger.addHandler(fh)
            except Exception as e:
                print(f"Warning: Could not create file logger at {log_path}: {e}")

            # Console handler if enabled
            if self.log_to_console:
                ch = logging.StreamHandler()
                ch.setLevel(logging.WARNING)
                ch.setFormatter(formatter)
                logger.addHandler(ch)

        return logger

    def evaluate(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate full system metrics against configured thresholds.
        
        :param metrics: Complete system metrics snapshot.
        :return: List of currently active alert records.
        """
        active_alerts: List[Dict[str, Any]] = []
        now = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. CPU Evaluation
        cpu_metrics = metrics.get("cpu", {})
        cpu_val = cpu_metrics.get("total_percent", 0.0)
        cpu_thresh = self.thresholds.get("cpu_percent", {})
        self._check_metric(
            metric_key="cpu_percent",
            display_name="CPU Total Utilization",
            current_val=cpu_val,
            unit="%",
            warning_thresh=cpu_thresh.get("warning"),
            critical_thresh=cpu_thresh.get("critical"),
            now=now,
            now_iso=now_iso,
            active_alerts=active_alerts
        )

        # 2. RAM Evaluation
        ram_metrics = metrics.get("memory", {}).get("ram", {})
        ram_val = ram_metrics.get("percent", 0.0)
        ram_thresh = self.thresholds.get("ram_percent", {})
        self._check_metric(
            metric_key="ram_percent",
            display_name="RAM Memory Utilization",
            current_val=ram_val,
            unit="%",
            warning_thresh=ram_thresh.get("warning"),
            critical_thresh=ram_thresh.get("critical"),
            now=now,
            now_iso=now_iso,
            active_alerts=active_alerts
        )

        # 3. Swap Evaluation
        swap_metrics = metrics.get("memory", {}).get("swap", {})
        swap_val = swap_metrics.get("percent", 0.0)
        swap_thresh = self.thresholds.get("swap_percent", {})
        self._check_metric(
            metric_key="swap_percent",
            display_name="Swap Utilization",
            current_val=swap_val,
            unit="%",
            warning_thresh=swap_thresh.get("warning"),
            critical_thresh=swap_thresh.get("critical"),
            now=now,
            now_iso=now_iso,
            active_alerts=active_alerts
        )

        # 4. Disk Partitions Evaluation
        disk_partitions = metrics.get("disk", {}).get("partitions", [])
        disk_thresh = self.thresholds.get("disk_percent", {})
        for part in disk_partitions:
            mount = part.get("mountpoint", "unknown")
            disk_val = part.get("percent", 0.0)
            self._check_metric(
                metric_key=f"disk_percent:{mount}",
                display_name=f"Disk Space ({mount})",
                current_val=disk_val,
                unit="%",
                warning_thresh=disk_thresh.get("warning"),
                critical_thresh=disk_thresh.get("critical"),
                now=now,
                now_iso=now_iso,
                active_alerts=active_alerts
            )

        return active_alerts

    def _check_metric(
        self,
        metric_key: str,
        display_name: str,
        current_val: float,
        unit: str,
        warning_thresh: Optional[float],
        critical_thresh: Optional[float],
        now: float,
        now_iso: str,
        active_alerts: List[Dict[str, Any]]
    ):
        """Helper to evaluate a numeric metric against warning/critical thresholds with cooldown and recovery."""
        severity = None
        threshold_val = None

        if critical_thresh is not None and current_val >= critical_thresh:
            severity = "CRITICAL"
            threshold_val = critical_thresh
        elif warning_thresh is not None and current_val >= warning_thresh:
            severity = "WARNING"
            threshold_val = warning_thresh

        # Case 1: Threshold is breached
        if severity:
            alert_record = {
                "metric_key": metric_key,
                "display_name": display_name,
                "severity": severity,
                "current_value": current_val,
                "threshold": threshold_val,
                "unit": unit,
                "timestamp": now_iso,
                "message": f"{display_name} is {current_val}{unit} (Threshold: {threshold_val}{unit})"
            }
            active_alerts.append(alert_record)

            # Check cooldown or state change
            prev_record = self.alert_history.get(metric_key)
            should_log = False

            if not prev_record:
                should_log = True
            elif prev_record["severity"] != severity:
                # Severity escalated or de-escalated
                should_log = True
            elif (now - prev_record["last_fired"]) >= self.cooldown_seconds:
                # Cooldown expired
                should_log = True

            if should_log:
                log_msg = f"[ALERT - {severity}] {alert_record['message']}"
                if severity == "CRITICAL":
                    self.logger.critical(log_msg)
                else:
                    self.logger.warning(log_msg)

                self.alert_history[metric_key] = {
                    "last_fired": now,
                    "severity": severity,
                    "value": current_val
                }

        # Case 2: Metric is within normal limits; check if previously alerting (recovery)
        else:
            if metric_key in self.alert_history:
                prev = self.alert_history.pop(metric_key)
                recovery_msg = f"[RECOVERY] {display_name} has returned to normal: {current_val}{unit} (was {prev['value']}{unit})"
                self.logger.info(recovery_msg)
