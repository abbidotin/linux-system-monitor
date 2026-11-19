"""
Unit tests for JSON report generation and Matplotlib chart rendering.
"""

import os
import json
import shutil
import tempfile
import unittest
from monitor.reporter import (
    get_system_metadata,
    generate_json_report,
    generate_visual_chart,
    format_text_summary
)


class TestReporter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_snapshot = {
            "timestamp": "2026-11-05T04:00:00Z",
            "metadata": get_system_metadata(),
            "cpu": {
                "total_percent": 35.5,
                "per_core_percent": [30.0, 41.0],
                "logical_cores": 2,
                "load_average": {"1_min": 1.2, "5_min": 1.0, "15_min": 0.8}
            },
            "memory": {
                "ram": {"percent": 62.4, "used_human": "4.20 GB", "total_human": "8.00 GB"},
                "swap": {"percent": 12.0, "used_human": "250.00 MB", "total_human": "2.00 GB"}
            },
            "disk": {
                "partitions": [
                    {"mountpoint": "/", "percent": 55.0, "used_human": "25.00 GB", "total_human": "50.00 GB", "fstype": "ext4"},
                    {"mountpoint": "/var", "percent": 78.5, "used_human": "15.00 GB", "total_human": "20.00 GB", "fstype": "ext4"}
                ],
                "io": {"read_speed_human": "120 KB/s", "write_speed_human": "450 KB/s"}
            },
            "network": {
                "overall": {
                    "download_speed_human": "1.50 MB/s",
                    "upload_speed_human": "200.00 KB/s",
                    "bytes_recv_human": "5.40 GB",
                    "bytes_sent_human": "1.20 GB",
                    "upload_speed_bytes_sec": 204800,
                    "download_speed_bytes_sec": 1572864
                },
                "interfaces": []
            },
            "processes": {
                "total_processes": 128,
                "status_distribution": {"running": 3, "sleeping": 125},
                "top_by_cpu": [
                    {"pid": 1024, "name": "python3", "cpu_percent": 18.5, "memory_percent": 4.2, "username": "root"},
                    {"pid": 2048, "name": "nginx", "cpu_percent": 12.1, "memory_percent": 2.1, "username": "www-data"}
                ]
            }
        }
        self.sample_history = [
            {"timestamp": "2026-11-05T03:59:00Z", "cpu_percent": 20.0, "ram_percent": 60.0, "net_sent_kb": 100, "net_recv_kb": 500},
            {"timestamp": "2026-11-05T03:59:30Z", "cpu_percent": 35.5, "ram_percent": 62.4, "net_sent_kb": 200, "net_recv_kb": 1500}
        ]
        self.thresholds = {
            "cpu_percent": {"warning": 75.0, "critical": 90.0},
            "ram_percent": {"warning": 80.0, "critical": 92.0}
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_json_report(self):
        alerts = [{"severity": "WARNING", "message": "High memory test"}]
        path = generate_json_report(
            snapshot=self.sample_snapshot,
            history=self.sample_history,
            active_alerts=alerts,
            output_dir=self.test_dir
        )
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("system_metadata", data)
        self.assertIn("active_alerts", data)
        self.assertIn("current_snapshot", data)
        self.assertIn("period_summary_stats", data)
        self.assertEqual(data["period_summary_stats"]["cpu"]["samples"], 2)

    def test_generate_visual_chart(self):
        chart_path = generate_visual_chart(
            history=self.sample_history,
            current_snapshot=self.sample_snapshot,
            thresholds=self.thresholds,
            output_dir=self.test_dir
        )
        self.assertIsNotNone(chart_path)
        self.assertTrue(os.path.exists(chart_path))
        self.assertGreater(os.path.getsize(chart_path), 5000)

    def test_format_text_summary(self):
        summary = format_text_summary(self.sample_snapshot, [])
        self.assertIn("SYSTEM HEALTH MONITORING REPORT", summary)
        self.assertIn("CPU Utilization", summary)
        self.assertIn("RAM Utilization", summary)
        self.assertIn("Disk Mounts", summary)
        self.assertIn("Network Activity", summary)


if __name__ == "__main__":
    unittest.main()
