"""
Unit tests for system metric collectors (CPU, Memory, Disk, Network, Process).
"""

import unittest
from monitor.cpu import get_cpu_metrics
from monitor.memory import get_memory_metrics, format_bytes
from monitor.disk import get_disk_partitions_usage, get_disk_io_metrics, get_disk_metrics
from monitor.network import get_network_metrics
from monitor.process import get_process_summary


class TestCollectors(unittest.TestCase):

    def test_cpu_metrics(self):
        cpu = get_cpu_metrics(sample_interval=None)
        self.assertIsInstance(cpu, dict)
        self.assertIn("total_percent", cpu)
        self.assertIn("per_core_percent", cpu)
        self.assertIn("logical_cores", cpu)
        self.assertGreaterEqual(cpu["logical_cores"], 1)
        self.assertGreaterEqual(cpu["total_percent"], 0.0)
        self.assertLessEqual(cpu["total_percent"], 100.0)

    def test_memory_metrics(self):
        mem = get_memory_metrics()
        self.assertIn("ram", mem)
        self.assertIn("swap", mem)
        ram = mem["ram"]
        self.assertGreater(ram["total_bytes"], 0)
        self.assertGreaterEqual(ram["percent"], 0.0)
        self.assertLessEqual(ram["percent"], 100.0)
        self.assertTrue(ram["total_human"].endswith(("B", "KB", "MB", "GB", "TB")))

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 5), "5.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 2), "2.00 GB")

    def test_disk_metrics(self):
        disk = get_disk_metrics()
        self.assertIn("partitions", disk)
        self.assertIn("io", disk)
        self.assertIsInstance(disk["partitions"], list)
        if disk["partitions"]:
            p = disk["partitions"][0]
            self.assertIn("mountpoint", p)
            self.assertIn("percent", p)
            self.assertGreaterEqual(p["percent"], 0.0)
            self.assertLessEqual(p["percent"], 100.0)

    def test_network_metrics(self):
        net = get_network_metrics()
        self.assertIn("overall", net)
        self.assertIn("interfaces", net)
        self.assertIsInstance(net["interfaces"], list)
        overall = net["overall"]
        self.assertIn("bytes_sent", overall)
        self.assertIn("bytes_recv", overall)
        self.assertIn("upload_speed_human", overall)

    def test_process_summary(self):
        proc = get_process_summary(top_n=5)
        self.assertIn("total_processes", proc)
        self.assertGreater(proc["total_processes"], 0)
        self.assertIn("top_by_cpu", proc)
        self.assertIn("top_by_memory", proc)
        self.assertLessEqual(len(proc["top_by_cpu"]), 5)
        if proc["top_by_cpu"]:
            p = proc["top_by_cpu"][0]
            self.assertIn("pid", p)
            self.assertIn("name", p)
            self.assertIn("cpu_percent", p)


if __name__ == "__main__":
    unittest.main()
