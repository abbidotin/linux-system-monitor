"""
Process Inspector and Resource Analyzer
Collects running process statistics, status breakdowns, and extracts top
resource-consuming processes (by CPU % and Memory %).
Handles permissions and transient processes safely.
"""

from datetime import datetime, timezone
import psutil
from typing import Dict, Any, List, Optional
from monitor.memory import format_bytes


def get_process_summary(top_n: int = 10) -> Dict[str, Any]:
    """
    Scan running processes and summarize state counts and top resource consumers.
    
    :param top_n: Number of top processes to return for CPU and Memory.
    :return: Summary dictionary containing total counts, state distributions,
             and top processes.
    """
    processes = []
    status_counts: Dict[str, int] = {}
    total_processes = 0

    # Fields to query
    attrs = [
        "pid", "name", "username", "status", "cpu_percent",
        "memory_percent", "memory_info", "create_time", "num_threads"
    ]

    for proc in psutil.process_iter(attrs=attrs):
        total_processes += 1
        try:
            pinfo = proc.info
            status = pinfo.get("status") or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

            mem_info = pinfo.get("memory_info")
            rss = mem_info.rss if mem_info else 0
            vms = mem_info.vms if mem_info else 0

            create_time_ts = pinfo.get("create_time") or 0
            create_time_str = ""
            if create_time_ts > 0:
                try:
                    create_time_str = datetime.fromtimestamp(create_time_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                except Exception:
                    create_time_str = str(create_time_ts)

            processes.append({
                "pid": pinfo.get("pid"),
                "name": pinfo.get("name") or "unknown",
                "username": pinfo.get("username") or "N/A",
                "status": status,
                "cpu_percent": round(pinfo.get("cpu_percent") or 0.0, 1),
                "memory_percent": round(pinfo.get("memory_percent") or 0.0, 1),
                "rss_bytes": rss,
                "vms_bytes": vms,
                "rss_human": format_bytes(rss),
                "num_threads": pinfo.get("num_threads") or 1,
                "started": create_time_str
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort top processes
    top_cpu = sorted(processes, key=lambda x: x["cpu_percent"], reverse=True)[:top_n]
    top_memory = sorted(processes, key=lambda x: x["memory_percent"], reverse=True)[:top_n]

    return {
        "total_processes": total_processes,
        "status_distribution": status_counts,
        "top_by_cpu": top_cpu,
        "top_by_memory": top_memory
    }
