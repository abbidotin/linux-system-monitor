"""
Disk Space and I/O Collector
Collects partition usage (total, used, free, percent) and disk I/O metrics.
Handles filesystem permission issues and filters pseudo-filesystems gracefully.
"""

import time
import psutil
from typing import Dict, Any, List, Optional
from monitor.memory import format_bytes


# Previous I/O state for rate calculation
_prev_io_counters = None
_prev_io_time = None

# Ignored Linux/Unix pseudo-filesystem types
IGNORED_FSTYPES = {
    "squashfs", "tmpfs", "devtmpfs", "overlay", "proc", "sysfs", "cgroup",
    "cgroup2", "pstore", "bpf", "autofs", "debugfs", "tracefs", "securityfs",
    "mqueue", "hugetlbfs", "devpts", "binfmt_misc", "fuse.lxcfs"
}


def get_disk_partitions_usage(include_pseudo: bool = False) -> List[Dict[str, Any]]:
    """
    Collect disk usage for all mounted disk partitions.
    
    :param include_pseudo: Whether to include virtual/pseudo filesystems (tmpfs, squashfs, etc.)
    :return: List of partition status dictionaries.
    """
    partitions_data = []
    seen_mounts = set()

    try:
        partitions = psutil.disk_partitions(all=include_pseudo)
    except Exception:
        partitions = []

    for part in partitions:
        mount = part.mountpoint
        if mount in seen_mounts:
            continue
        
        fstype = part.fstype.lower() if part.fstype else ""
        if not include_pseudo and (fstype in IGNORED_FSTYPES or part.device.startswith("/dev/loop")):
            continue

        try:
            usage = psutil.disk_usage(mount)
            seen_mounts.add(mount)
            partitions_data.append({
                "device": part.device,
                "mountpoint": mount,
                "fstype": part.fstype,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": round(usage.percent, 1),
                "total_human": format_bytes(usage.total),
                "used_human": format_bytes(usage.used),
                "free_human": format_bytes(usage.free)
            })
        except (PermissionError, OSError):
            # Skip mount points that can't be accessed (e.g. root-only or unmounted)
            continue

    return partitions_data


def get_disk_io_metrics() -> Dict[str, Any]:
    """
    Collect disk I/O read/write counters and rates.
    
    :return: Dictionary containing cumulative I/O and rates per second.
    """
    global _prev_io_counters, _prev_io_time
    now = time.time()

    try:
        current_io = psutil.disk_io_counters()
    except Exception:
        current_io = None

    if not current_io:
        return {
            "available": False,
            "read_bytes": 0,
            "write_bytes": 0,
            "read_count": 0,
            "write_count": 0,
            "read_bytes_per_sec": 0.0,
            "write_bytes_per_sec": 0.0,
            "read_speed_human": "0 B/s",
            "write_speed_human": "0 B/s"
        }

    read_rate = 0.0
    write_rate = 0.0

    if _prev_io_counters and _prev_io_time:
        time_delta = now - _prev_io_time
        if time_delta > 0:
            read_delta = max(0, current_io.read_bytes - _prev_io_counters.read_bytes)
            write_delta = max(0, current_io.write_bytes - _prev_io_counters.write_bytes)
            read_rate = read_delta / time_delta
            write_rate = write_delta / time_delta

    _prev_io_counters = current_io
    _prev_io_time = now

    return {
        "available": True,
        "read_bytes": current_io.read_bytes,
        "write_bytes": current_io.write_bytes,
        "read_count": current_io.read_count,
        "write_count": current_io.write_count,
        "read_time_ms": getattr(current_io, "read_time", 0),
        "write_time_ms": getattr(current_io, "write_time", 0),
        "read_bytes_per_sec": round(read_rate, 1),
        "write_bytes_per_sec": round(write_rate, 1),
        "read_speed_human": f"{format_bytes(int(read_rate))}/s",
        "write_speed_human": f"{format_bytes(int(write_rate))}/s"
    }


def get_disk_metrics(include_pseudo: bool = False) -> Dict[str, Any]:
    """
    Collect complete disk metrics (partitions and I/O).
    """
    return {
        "partitions": get_disk_partitions_usage(include_pseudo=include_pseudo),
        "io": get_disk_io_metrics()
    }
