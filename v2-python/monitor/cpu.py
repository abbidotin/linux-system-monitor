"""
CPU Metrics Collector
Collects total and per-core utilization, frequency, load averages, and CPU times.
Cross-platform support for Linux and Windows.
"""

import os
import psutil
from typing import Dict, Any, List, Optional


def get_cpu_metrics(sample_interval: Optional[float] = None) -> Dict[str, Any]:
    """
    Collect comprehensive CPU utilization statistics.
    
    :param sample_interval: Seconds to block for measuring utilization. 
                            Pass None for non-blocking since last call.
    :return: Dictionary containing detailed CPU metrics.
    """
    # Utilization percentage
    total_percent = psutil.cpu_percent(interval=sample_interval)
    per_core = psutil.cpu_percent(interval=sample_interval, percpu=True)
    
    # Core counts
    logical_cores = psutil.cpu_count(logical=True) or 1
    physical_cores = psutil.cpu_count(logical=False) or logical_cores
    
    # Frequency
    freq_data = None
    try:
        freq = psutil.cpu_freq()
        if freq:
            freq_data = {
                "current_mhz": round(freq.current, 1) if freq.current else None,
                "min_mhz": round(freq.min, 1) if freq.min else None,
                "max_mhz": round(freq.max, 1) if freq.max else None
            }
    except Exception:
        pass

    # Load average (1, 5, 15 minutes) - Standard on Linux/Unix
    load_avg = None
    if hasattr(os, "getloadavg"):
        try:
            l1, l5, l15 = os.getloadavg()
            load_avg = {
                "1_min": round(l1, 2),
                "5_min": round(l5, 2),
                "15_min": round(l15, 2),
                "load_per_core_1min": round(l1 / logical_cores, 2)
            }
        except (OSError, AttributeError):
            pass
    elif hasattr(psutil, "getloadavg"):
        try:
            l1, l5, l15 = psutil.getloadavg()
            load_avg = {
                "1_min": round(l1, 2),
                "5_min": round(l5, 2),
                "15_min": round(l15, 2),
                "load_per_core_1min": round(l1 / logical_cores, 2)
            }
        except Exception:
            pass

    # CPU Times breakdown
    times_breakdown = {}
    try:
        times = psutil.cpu_times_percent(interval=None)
        times_breakdown["user"] = round(getattr(times, "user", 0.0), 1)
        times_breakdown["system"] = round(getattr(times, "system", 0.0), 1)
        times_breakdown["idle"] = round(getattr(times, "idle", 0.0), 1)
        # Linux specific fields
        if hasattr(times, "iowait"):
            times_breakdown["iowait"] = round(times.iowait, 1)
        if hasattr(times, "steal"):
            times_breakdown["steal"] = round(times.steal, 1)
        if hasattr(times, "nice"):
            times_breakdown["nice"] = round(times.nice, 1)
    except Exception:
        pass

    # Context switches and interrupts
    cpu_stats = {}
    try:
        stats = psutil.cpu_stats()
        cpu_stats["ctx_switches"] = stats.ctx_switches
        cpu_stats["interrupts"] = stats.interrupts
        if hasattr(stats, "soft_interrupts"):
            cpu_stats["soft_interrupts"] = stats.soft_interrupts
    except Exception:
        pass

    return {
        "total_percent": round(total_percent, 1),
        "per_core_percent": [round(c, 1) for c in per_core],
        "logical_cores": logical_cores,
        "physical_cores": physical_cores,
        "frequency": freq_data,
        "load_average": load_avg,
        "times_percent": times_breakdown,
        "stats": cpu_stats
    }
