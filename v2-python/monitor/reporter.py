"""
Periodic System Report Generator
Generates structured JSON reports, human-readable terminal summaries,
and visual Matplotlib trend charts (configured with headless 'Agg' backend
for cross-platform and headless server compatibility).
"""

import os
import json
import socket
import platform
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Ensure matplotlib uses a non-GUI backend suitable for headless Linux servers
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def get_system_metadata() -> Dict[str, Any]:
    """Collect static host metadata."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }


def generate_json_report(
    snapshot: Dict[str, Any],
    history: List[Dict[str, Any]],
    active_alerts: List[Dict[str, Any]],
    output_dir: str = "reports"
) -> str:
    """
    Generate and save a timestamped JSON system report.
    
    :return: Filepath of the generated JSON report.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_filename = f"system_report_{timestamp_str}.json"
    report_path = os.path.join(output_dir, report_filename)
    latest_path = os.path.join(output_dir, "latest_report.json")

    # Compute period summary stats from history if available
    summary_stats = {}
    if history:
        cpu_vals = [h.get("cpu_percent", 0.0) for h in history if "cpu_percent" in h]
        ram_vals = [h.get("ram_percent", 0.0) for h in history if "ram_percent" in h]
        if cpu_vals:
            summary_stats["cpu"] = {
                "avg_percent": round(sum(cpu_vals) / len(cpu_vals), 1),
                "min_percent": round(min(cpu_vals), 1),
                "max_percent": round(max(cpu_vals), 1),
                "samples": len(cpu_vals)
            }
        if ram_vals:
            summary_stats["ram"] = {
                "avg_percent": round(sum(ram_vals) / len(ram_vals), 1),
                "min_percent": round(min(ram_vals), 1),
                "max_percent": round(max(ram_vals), 1),
                "samples": len(ram_vals)
            }

    report_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_metadata": get_system_metadata(),
        "active_alerts": active_alerts,
        "period_summary_stats": summary_stats,
        "current_snapshot": snapshot
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    # Also write / update latest_report.json symlink/copy
    try:
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)
    except Exception:
        pass

    return report_path


def generate_visual_chart(
    history: List[Dict[str, Any]],
    current_snapshot: Dict[str, Any],
    thresholds: Dict[str, Any],
    output_dir: str = "reports"
) -> Optional[str]:
    """
    Generate a multi-panel visual diagnostic chart using Matplotlib.
    
    1. CPU & RAM utilization time-series graph with warning/critical threshold lines.
    2. Network bandwidth transfer rate time-series graph (KB/s).
    3. Disk space utilization per partition (colored bar chart).
    4. Top 5 CPU-consuming processes bar chart.
    
    :return: Filepath of the generated PNG chart, or None if skipped.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    chart_filename = f"system_report_{timestamp_str}.png"
    chart_path = os.path.join(output_dir, chart_filename)
    latest_chart = os.path.join(output_dir, "latest_report.png")

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.subplots_adjust(top=0.92, bottom=0.08, left=0.12, right=0.95, hspace=0.35, wspace=0.30)
    fig.suptitle(
        f"System Health Diagnostic Report - {socket.gethostname()} ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')})",
        fontsize=14,
        fontweight="bold"
    )

    # ---------------- 1. CPU & RAM Usage Timeline ----------------
    ax_cpu_ram = axes[0, 0]
    time_points = list(range(len(history)))
    cpu_history = [h.get("cpu_percent", 0.0) for h in history]
    ram_history = [h.get("ram_percent", 0.0) for h in history]

    if not time_points:
        time_points = [0]
        cpu_history = [current_snapshot.get("cpu", {}).get("total_percent", 0.0)]
        ram_history = [current_snapshot.get("memory", {}).get("ram", {}).get("percent", 0.0)]

    ax_cpu_ram.plot(time_points, cpu_history, label="CPU %", color="#1f77b4", linewidth=2)
    ax_cpu_ram.plot(time_points, ram_history, label="RAM %", color="#2ca02c", linewidth=2)

    # Threshold horizontal reference lines
    cpu_warn = thresholds.get("cpu_percent", {}).get("warning")
    cpu_crit = thresholds.get("cpu_percent", {}).get("critical")
    if cpu_warn:
        ax_cpu_ram.axhline(cpu_warn, color="#ff7f0e", linestyle="--", alpha=0.7, label=f"CPU Warn ({cpu_warn}%)")
    if cpu_crit:
        ax_cpu_ram.axhline(cpu_crit, color="#d62728", linestyle="--", alpha=0.7, label=f"CPU Crit ({cpu_crit}%)")

    ax_cpu_ram.set_title("Resource Utilization Over Time", fontsize=11, fontweight="bold")
    ax_cpu_ram.set_xlabel("Sample Points")
    ax_cpu_ram.set_ylabel("Utilization (%)")
    ax_cpu_ram.set_ylim(0, 105)
    ax_cpu_ram.legend(loc="upper left", fontsize=8)
    ax_cpu_ram.grid(True, linestyle=":", alpha=0.6)

    # ---------------- 2. Network Throughput Timeline ----------------
    ax_net = axes[0, 1]
    net_up = [h.get("net_sent_kb", 0.0) for h in history]
    net_down = [h.get("net_recv_kb", 0.0) for h in history]
    if not net_up:
        net_up = [current_snapshot.get("network", {}).get("overall", {}).get("upload_speed_bytes_sec", 0.0) / 1024.0]
        net_down = [current_snapshot.get("network", {}).get("overall", {}).get("download_speed_bytes_sec", 0.0) / 1024.0]

    ax_net.plot(time_points, net_down, label="Download (KB/s)", color="#9467bd", linewidth=2)
    ax_net.plot(time_points, net_up, label="Upload (KB/s)", color="#e377c2", linewidth=2)
    ax_net.set_title("Network Throughput (KB/s)", fontsize=11, fontweight="bold")
    ax_net.set_xlabel("Sample Points")
    ax_net.set_ylabel("Speed (KB/s)")
    ax_net.legend(loc="upper left", fontsize=8)
    ax_net.grid(True, linestyle=":", alpha=0.6)

    # ---------------- 3. Disk Space Per Partition ----------------
    ax_disk = axes[1, 0]
    partitions = current_snapshot.get("disk", {}).get("partitions", [])
    if partitions:
        mounts = [p.get("mountpoint", "N/A") for p in partitions][:6]
        percentages = [p.get("percent", 0.0) for p in partitions][:6]
        colors = []
        for p in percentages:
            if p >= 90:
                colors.append("#d62728")  # red
            elif p >= 75:
                colors.append("#ff7f0e")  # orange
            else:
                colors.append("#2ca02c")  # green

        bars = ax_disk.barh(mounts, percentages, color=colors, height=0.55)
        ax_disk.set_xlim(0, 105)
        ax_disk.set_title("Disk Space Allocation (%)", fontsize=11, fontweight="bold")
        ax_disk.set_xlabel("Used Space (%)")
        ax_disk.grid(True, axis="x", linestyle=":", alpha=0.6)

        for bar, pct in zip(bars, percentages):
            ax_disk.text(pct + 1, bar.get_y() + bar.get_height() / 2, f"{pct}%", va="center", fontsize=8)
    else:
        ax_disk.text(0.5, 0.5, "No partitions detected", ha="center", va="center")

    # ---------------- 4. Top CPU Processes ----------------
    ax_proc = axes[1, 1]
    top_cpu = current_snapshot.get("processes", {}).get("top_by_cpu", [])[:5]
    if top_cpu:
        p_names = [f"{p.get('name', 'unk')[:12]} ({p.get('pid')})" for p in reversed(top_cpu)]
        p_cpu = [p.get("cpu_percent", 0.0) for p in reversed(top_cpu)]
        bars = ax_proc.barh(p_names, p_cpu, color="#17becf", height=0.55)
        ax_proc.set_title("Top 5 Processes by CPU %", fontsize=11, fontweight="bold")
        ax_proc.set_xlabel("CPU (%)")
        ax_proc.grid(True, axis="x", linestyle=":", alpha=0.6)

        for bar, pct in zip(bars, p_cpu):
            ax_proc.text(pct + 0.5, bar.get_y() + bar.get_height() / 2, f"{pct}%", va="center", fontsize=8)
    else:
        ax_proc.text(0.5, 0.5, "No process metrics", ha="center", va="center")

    plt.savefig(chart_path, dpi=120)
    try:
        plt.savefig(latest_chart, dpi=120)
    except Exception:
        pass
    plt.close(fig)

    return chart_path


def format_text_summary(snapshot: Dict[str, Any], active_alerts: List[Dict[str, Any]]) -> str:
    """Format snapshot and alerts into an aesthetic, readable terminal report."""
    lines = []
    lines.append("=" * 65)
    lines.append("              SYSTEM HEALTH MONITORING REPORT")
    lines.append("=" * 65)

    meta = snapshot.get("metadata", {})
    lines.append(f" Host:     {meta.get('hostname')} | Platform: {meta.get('system')} {meta.get('release')}")
    lines.append(f" Time:     {snapshot.get('timestamp')}")
    lines.append("-" * 65)

    # Alerts Banner
    if active_alerts:
        lines.append(" [!] ACTIVE ALERTS:")
        for a in active_alerts:
            lines.append(f"     - [{a.get('severity')}] {a.get('message')}")
        lines.append("-" * 65)
    else:
        lines.append(" [✓] System Status: HEALTHY (No active threshold alerts)")
        lines.append("-" * 65)

    # CPU
    cpu = snapshot.get("cpu", {})
    load = cpu.get("load_average")
    load_str = f"1m: {load.get('1_min')}, 5m: {load.get('5_min')}, 15m: {load.get('15_min')}" if load else "N/A"
    lines.append(f" CPU Utilization:  {cpu.get('total_percent')}% (Cores: {cpu.get('logical_cores')})")
    lines.append(f" Load Average:     {load_str}")

    # RAM & Swap
    mem = snapshot.get("memory", {})
    ram = mem.get("ram", {})
    swap = mem.get("swap", {})
    lines.append(f" RAM Utilization:  {ram.get('percent')}% (Used: {ram.get('used_human')} / {ram.get('total_human')})")
    lines.append(f" Swap Memory:      {swap.get('percent')}% (Used: {swap.get('used_human')} / {swap.get('total_human')})")

    # Disk
    lines.append("-" * 65)
    lines.append(" Disk Mounts:")
    partitions = snapshot.get("disk", {}).get("partitions", [])
    for p in partitions:
        lines.append(f"   {p.get('mountpoint', 'N/A'):<15} {p.get('percent'):>5}% used ({p.get('used_human')} / {p.get('total_human')}) [{p.get('fstype')}]")
    io = snapshot.get("disk", {}).get("io", {})
    lines.append(f" Disk I/O Rate:    Read: {io.get('read_speed_human', '0 B/s')}, Write: {io.get('write_speed_human', '0 B/s')}")

    # Network
    lines.append("-" * 65)
    net_overall = snapshot.get("network", {}).get("overall", {})
    lines.append(f" Network Activity: Download: {net_overall.get('download_speed_human', '0 B/s')} | Upload: {net_overall.get('upload_speed_human', '0 B/s')}")
    lines.append(f" Total Transferred: Recv: {net_overall.get('bytes_recv_human')} | Sent: {net_overall.get('bytes_sent_human')}")

    # Processes
    lines.append("-" * 65)
    procs = snapshot.get("processes", {})
    lines.append(f" Total Processes:  {procs.get('total_processes')} | State: {procs.get('status_distribution', {})}")
    lines.append(" Top Processes by CPU:")
    lines.append(f"   {'PID':<8} {'Name':<20} {'CPU %':<8} {'Memory %':<10} {'User':<12}")
    for p in procs.get("top_by_cpu", [])[:5]:
        name = p.get('name', 'N/A')[:18]
        user = (p.get('username') or 'N/A')[:11]
        lines.append(f"   {p.get('pid'):<8} {name:<20} {p.get('cpu_percent'):<8} {p.get('memory_percent'):<10} {user:<12}")

    lines.append("=" * 65)
    return "\n".join(lines)
