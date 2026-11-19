"""
Memory Metrics Collector
Collects RAM utilization (total, used, available, buffers, cache) and Swap utilization.
Provides byte conversion utilities for clean reporting.
"""

import psutil
from typing import Dict, Any


def format_bytes(bytes_value: int) -> str:
    """Format bytes into a human-readable string (KB, MB, GB, TB)."""
    if bytes_value is None or bytes_value < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def get_memory_metrics() -> Dict[str, Any]:
    """
    Collect comprehensive Virtual RAM and Swap memory utilization.
    
    :return: Dictionary containing memory metrics and formatted values.
    """
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()

    ram_data = {
        "total_bytes": vm.total,
        "available_bytes": vm.available,
        "used_bytes": vm.used,
        "free_bytes": vm.free,
        "percent": round(vm.percent, 1),
        "total_human": format_bytes(vm.total),
        "available_human": format_bytes(vm.available),
        "used_human": format_bytes(vm.used),
        "free_human": format_bytes(vm.free)
    }

    # Linux-specific virtual memory attributes
    if hasattr(vm, "buffers"):
        ram_data["buffers_bytes"] = vm.buffers
        ram_data["buffers_human"] = format_bytes(vm.buffers)
    if hasattr(vm, "cached"):
        ram_data["cached_bytes"] = vm.cached
        ram_data["cached_human"] = format_bytes(vm.cached)
    if hasattr(vm, "shared"):
        ram_data["shared_bytes"] = vm.shared
        ram_data["shared_human"] = format_bytes(vm.shared)

    swap_data = {
        "total_bytes": swap.total,
        "used_bytes": swap.used,
        "free_bytes": swap.free,
        "percent": round(swap.percent, 1),
        "total_human": format_bytes(swap.total),
        "used_human": format_bytes(swap.used),
        "free_human": format_bytes(swap.free),
        "sin_bytes": getattr(swap, "sin", 0),
        "sout_bytes": getattr(swap, "sout", 0)
    }

    return {
        "ram": ram_data,
        "swap": swap_data
    }
