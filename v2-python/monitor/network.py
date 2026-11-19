"""
Network Statistics and Throughput Collector
Collects interface status, error/drop statistics, cumulative I/O,
and calculates upload/download bandwidth transfer rates.
"""

import time
import socket
import psutil
from typing import Dict, Any, List, Optional
from monitor.memory import format_bytes


_prev_net_io = None
_prev_net_time = None
_prev_nic_io = {}


def get_network_metrics() -> Dict[str, Any]:
    """
    Collect comprehensive network metrics including per-interface stats
    and real-time transfer rates.
    
    :return: Dictionary containing network metrics and bandwidth speeds.
    """
    global _prev_net_io, _prev_net_time, _prev_nic_io
    now = time.time()

    # Total network I/O
    try:
        total_io = psutil.net_io_counters(pernic=False)
    except Exception:
        total_io = None

    # Per-interface I/O
    try:
        nics_io = psutil.net_io_counters(pernic=True)
    except Exception:
        nics_io = {}

    # Interface stats (link status, speed, MTU)
    try:
        if_stats = psutil.net_if_stats()
    except Exception:
        if_stats = {}

    # Interface addresses
    try:
        if_addrs = psutil.net_if_addrs()
    except Exception:
        if_addrs = {}

    # Calculate overall upload/download transfer rates
    bytes_sent_per_sec = 0.0
    bytes_recv_per_sec = 0.0

    if total_io and _prev_net_io and _prev_net_time:
        time_delta = now - _prev_net_time
        if time_delta > 0:
            sent_delta = max(0, total_io.bytes_sent - _prev_net_io.bytes_sent)
            recv_delta = max(0, total_io.bytes_recv - _prev_net_io.bytes_recv)
            bytes_sent_per_sec = sent_delta / time_delta
            bytes_recv_per_sec = recv_delta / time_delta

    _prev_net_io = total_io
    _prev_net_time = now

    # Per-interface details
    interfaces_data = []
    for nic_name, nic_counter in nics_io.items():
        # Link stats
        stats = if_stats.get(nic_name)
        is_up = stats.isup if stats else False
        speed_mbps = stats.speed if stats else 0
        mtu = stats.mtu if stats else 0

        # Rate per NIC
        nic_sent_rate = 0.0
        nic_recv_rate = 0.0
        if nic_name in _prev_nic_io and _prev_net_time:
            p_sent, p_recv, p_time = _prev_nic_io[nic_name]
            dt = now - p_time
            if dt > 0:
                nic_sent_rate = max(0, nic_counter.bytes_sent - p_sent) / dt
                nic_recv_rate = max(0, nic_counter.bytes_recv - p_recv) / dt

        _prev_nic_io[nic_name] = (nic_counter.bytes_sent, nic_counter.bytes_recv, now)

        # IP addresses
        addresses = []
        for addr in if_addrs.get(nic_name, []):
            if addr.family == socket.AF_INET:
                addresses.append({"family": "IPv4", "address": addr.address, "netmask": addr.netmask})
            elif getattr(socket, "AF_INET6", None) and addr.family == socket.AF_INET6:
                addresses.append({"family": "IPv6", "address": addr.address.split("%")[0]})

        interfaces_data.append({
            "interface": nic_name,
            "is_up": is_up,
            "speed_mbps": speed_mbps,
            "mtu": mtu,
            "bytes_sent": nic_counter.bytes_sent,
            "bytes_recv": nic_counter.bytes_recv,
            "bytes_sent_human": format_bytes(nic_counter.bytes_sent),
            "bytes_recv_human": format_bytes(nic_counter.bytes_recv),
            "packets_sent": nic_counter.packets_sent,
            "packets_recv": nic_counter.packets_recv,
            "errors_in": nic_counter.errin,
            "errors_out": nic_counter.errout,
            "drop_in": nic_counter.dropin,
            "drop_out": nic_counter.dropout,
            "upload_speed_bytes_sec": round(nic_sent_rate, 1),
            "download_speed_bytes_sec": round(nic_recv_rate, 1),
            "upload_speed_human": f"{format_bytes(int(nic_sent_rate))}/s",
            "download_speed_human": f"{format_bytes(int(nic_recv_rate))}/s",
            "addresses": addresses
        })

    # Sort interfaces so active ones are first
    interfaces_data.sort(key=lambda x: (x["is_up"], x["bytes_sent"] + x["bytes_recv"]), reverse=True)

    return {
        "overall": {
            "bytes_sent": total_io.bytes_sent if total_io else 0,
            "bytes_recv": total_io.bytes_recv if total_io else 0,
            "bytes_sent_human": format_bytes(total_io.bytes_sent) if total_io else "0 B",
            "bytes_recv_human": format_bytes(total_io.bytes_recv) if total_io else "0 B",
            "packets_sent": total_io.packets_sent if total_io else 0,
            "packets_recv": total_io.packets_recv if total_io else 0,
            "errors_in": total_io.errin if total_io else 0,
            "errors_out": total_io.errout if total_io else 0,
            "upload_speed_bytes_sec": round(bytes_sent_per_sec, 1),
            "download_speed_bytes_sec": round(bytes_recv_per_sec, 1),
            "upload_speed_human": f"{format_bytes(int(bytes_sent_per_sec))}/s",
            "download_speed_human": f"{format_bytes(int(bytes_recv_per_sec))}/s"
        },
        "interfaces": interfaces_data
    }
