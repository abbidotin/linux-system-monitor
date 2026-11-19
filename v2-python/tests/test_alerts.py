"""
Unit tests for threshold alert evaluation, cooldown, and recovery logging.
"""

import unittest
import logging
from monitor.alerts import AlertManager


class MockLogger:
    """Mock logger capturing calls for testing."""
    def __init__(self):
        self.logs = []

    def info(self, msg):
        self.logs.append(("INFO", msg))

    def warning(self, msg):
        self.logs.append(("WARNING", msg))

    def critical(self, msg):
        self.logs.append(("CRITICAL", msg))


class TestAlerts(unittest.TestCase):

    def setUp(self):
        self.config = {
            "thresholds": {
                "cpu_percent": {"warning": 70.0, "critical": 90.0},
                "ram_percent": {"warning": 80.0, "critical": 95.0},
                "swap_percent": {"warning": 50.0, "critical": 80.0},
                "disk_percent": {"warning": 85.0, "critical": 95.0}
            },
            "alerts": {
                "cooldown_seconds": 60,
                "log_alerts_to_console": False
            },
            "paths": {
                "log_file": "logs/test_monitor.log"
            }
        }
        self.mock_logger = MockLogger()
        self.alert_manager = AlertManager(self.config, logger=self.mock_logger)

    def test_normal_metrics_no_alerts(self):
        metrics = {
            "cpu": {"total_percent": 25.0},
            "memory": {
                "ram": {"percent": 45.0},
                "swap": {"percent": 10.0}
            },
            "disk": {
                "partitions": [{"mountpoint": "/", "percent": 40.0}]
            }
        }
        alerts = self.alert_manager.evaluate(metrics)
        self.assertEqual(len(alerts), 0)
        self.assertEqual(len(self.mock_logger.logs), 0)

    def test_warning_threshold_breach(self):
        metrics = {
            "cpu": {"total_percent": 75.0},  # Warning is 70.0
            "memory": {
                "ram": {"percent": 45.0},
                "swap": {"percent": 10.0}
            },
            "disk": {
                "partitions": [{"mountpoint": "/", "percent": 40.0}]
            }
        }
        alerts = self.alert_manager.evaluate(metrics)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["severity"], "WARNING")
        self.assertEqual(alerts[0]["metric_key"], "cpu_percent")
        self.assertEqual(len(self.mock_logger.logs), 1)
        self.assertEqual(self.mock_logger.logs[0][0], "WARNING")

    def test_critical_threshold_breach(self):
        metrics = {
            "cpu": {"total_percent": 95.0},  # Critical is 90.0
            "memory": {
                "ram": {"percent": 45.0},
                "swap": {"percent": 10.0}
            },
            "disk": {
                "partitions": [{"mountpoint": "/", "percent": 40.0}]
            }
        }
        alerts = self.alert_manager.evaluate(metrics)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["severity"], "CRITICAL")
        self.assertEqual(self.mock_logger.logs[0][0], "CRITICAL")

    def test_cooldown_deduplication(self):
        metrics = {
            "cpu": {"total_percent": 75.0},
            "memory": {"ram": {"percent": 40.0}, "swap": {"percent": 0.0}},
            "disk": {"partitions": []}
        }
        # First call triggers log
        self.alert_manager.evaluate(metrics)
        self.assertEqual(len(self.mock_logger.logs), 1)

        # Second call within cooldown does not duplicate log
        self.alert_manager.evaluate(metrics)
        self.assertEqual(len(self.mock_logger.logs), 1)

    def test_recovery_logging(self):
        # Step 1: Breach threshold
        metrics_high = {
            "cpu": {"total_percent": 80.0},
            "memory": {"ram": {"percent": 40.0}, "swap": {"percent": 0.0}},
            "disk": {"partitions": []}
        }
        self.alert_manager.evaluate(metrics_high)
        self.assertEqual(len(self.mock_logger.logs), 1)

        # Step 2: Metric normalizes
        metrics_normal = {
            "cpu": {"total_percent": 30.0},
            "memory": {"ram": {"percent": 40.0}, "swap": {"percent": 0.0}},
            "disk": {"partitions": []}
        }
        alerts = self.alert_manager.evaluate(metrics_normal)
        self.assertEqual(len(alerts), 0)
        # Should record an INFO recovery message
        self.assertEqual(len(self.mock_logger.logs), 2)
        self.assertEqual(self.mock_logger.logs[1][0], "INFO")
        self.assertIn("RECOVERY", self.mock_logger.logs[1][1])


if __name__ == "__main__":
    unittest.main()
