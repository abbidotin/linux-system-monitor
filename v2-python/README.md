# Cross-Platform System Health Monitor (Python)

A lightweight, production-grade cross-platform system monitoring agent for **Linux and Windows** built in Python using `psutil`, `logging`, and `matplotlib`. It continuously tracks system health, enforces threshold-based alerting, logs diagnostic events, and automatically produces periodic JSON summaries and visual performance charts.

---

## Features

1. **CPU Usage Monitoring**
   - Overall CPU utilization (%) and per-core breakdown.
   - CPU clock frequency (current, min, max in MHz).
   - Standard 1, 5, and 15-minute load averages (with per-core normalized load on Linux; simulated equivalent on Windows).
   - CPU time breakdown (`user`, `system`, `idle`, and `iowait`/`steal`/`nice` when available).
   - Context switches and interrupt counters.

2. **RAM & Swap Utilization**
   - Total, used, free, and available virtual memory with usage percentages.
   - Human-readable byte formatting (MB, GB, TB).
   - Virtual memory buffer/cached metrics (Linux) and swap/pagefile space monitoring (Windows & Linux).

3. **Disk Space & I/O Monitoring**
   - Automatic discovery of mounted filesystem partitions (root `/`, data drives, Windows drive letters `C:\`, `D:\`).
   - Total, used, free disk space, and percent capacity per mountpoint.
   - Intelligent filtering of virtual and pseudo-filesystems (`squashfs`, `tmpfs`, `cgroup`, etc.).
   - Real-time disk I/O metrics: read/write counts, total transfer bytes, and read/write transfer rates (KB/s, MB/s).

4. **Running Process Inspection**
   - Active process inventory and lifecycle state distribution (`running`, `sleeping`, `stopped`, etc.).
   - Top resource-consuming processes sorted by CPU % and Memory %.
   - Process attributes: PID, process name, owner/username, status, CPU %, memory %, RSS memory, thread count, start time.

5. **Network Statistics & Bandwidth Throughput**
   - Per-interface link status (up/down, interface speed in Mbps, MTU, assigned IPv4/IPv6 addresses).
   - Cumulative sent/received bytes and packet counts.
   - Network error and drop tracking (`errin`, `errout`, `dropin`, `dropout`).
   - Real-time network throughput calculation (Upload and Download bandwidth in KB/s and MB/s).

6. **Threshold-Based Alerts & Audit Logging**
   - Configurable `WARNING` and `CRITICAL` thresholds for CPU, RAM, Swap, and Disk capacity.
   - Alert cooldown / deduplication logic to prevent log flooding during persistent load.
   - Automatic **recovery detection** when metrics return within safe operating limits.
   - Structured logging to rotating file (`logs/monitor.log`) and standard error/console using Python's standard `logging` module.

7. **Periodic System Reports & Visual Analytics**
   - **Structured JSON Reports**: Saves machine-readable snapshots (`reports/system_report_YYYYMMDD_HHMMSS.json` and `latest_report.json`) containing host metadata, all metrics, active alerts, and period statistical summaries (avg, min, max).
   - **Matplotlib Visual Trend Charts**: Generates multi-panel performance figures (`reports/system_report_YYYYMMDD_HHMMSS.png` and `latest_report.png`) using the headless `Agg` backend (works seamlessly on desktop and headless servers without display servers):
     - Resource utilization timeline (CPU & RAM vs threshold reference lines).
     - Network throughput timeline (Download & Upload KB/s).
     - Partition capacity horizontal bar chart with color-coded warning levels.
     - Top CPU-consuming processes bar chart.

---

## Directory Structure

```
system-health-monitor/
├── config/
│   └── config.json            # Configurable thresholds, intervals, paths
├── monitor/
│   ├── __init__.py            # Module exports
│   ├── cpu.py                 # CPU metrics & load average collector
│   ├── memory.py              # Virtual memory & swap collector
│   ├── disk.py                # Disk partitions, capacity & I/O stats
│   ├── network.py             # Network interfaces & bandwidth calculator
│   ├── process.py             # Process analyzer & resource ranking
│   ├── alerts.py              # Threshold evaluator, cooldown & logger
│   ├── reporter.py            # JSON reporter & Matplotlib chart visualizer
│   └── engine.py              # Central orchestrator & monitoring loop
├── reports/                   # Output folder for JSON reports and PNG charts
├── logs/                      # Output folder for alert and system audit logs
├── tests/                     # Unit test suite
│   ├── __init__.py
│   ├── test_collectors.py
│   ├── test_alerts.py
│   └── test_reporter.py
├── main.py                    # Main CLI application
├── run_monitor.sh             # Linux/macOS launcher script
├── run_monitor.bat            # Windows launcher script
├── system_monitor.service     # Linux systemd service unit template
├── requirements.txt           # Dependencies (psutil, matplotlib)
└── README.md
```

---

## Installation & Quickstart

### Prerequisites
- Python 3.8+
- Operating System: **Linux** (Ubuntu, Debian, CentOS, Fedora, etc.) or **Windows** (10, 11, Server).

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

---

## Usage Modes

### 1. Instant Diagnostic Snapshot (`snapshot`)
Captures an immediate system health snapshot, prints a formatted summary in the terminal, and exports JSON & PNG visual reports:

- **Windows:**
  ```powershell
  py -3 main.py snapshot
  # or use the batch launcher:
  .\run_monitor.bat snapshot
  ```
- **Linux:**
  ```bash
  python3 main.py snapshot
  # or use the shell launcher:
  ./run_monitor.sh snapshot
  ```

---

### 2. Live Terminal Watch Dashboard (`watch`)
Provides a real-time updating terminal dashboard (like `htop` / `Task Manager`):

- **Windows:**
  ```powershell
  py -3 main.py watch
  ```
- **Linux:**
  ```bash
  python3 main.py watch
  ```

---

### 3. Continuous Background Daemon (`daemon`)
Runs continuously as a monitoring service, checking thresholds, logging alerts, and generating periodic reports according to `config/config.json`:

- **Windows:**
  ```powershell
  py -3 main.py daemon
  ```
- **Linux:**
  ```bash
  python3 main.py daemon
  # Or run in background with nohup:
  nohup python3 main.py daemon > /dev/null 2>&1 &
  ```

#### CLI Options:
- `-c, --config`: Path to custom configuration file (default: `config/config.json`).
- `-d, --duration`: Run for N seconds and then exit cleanly (e.g. `--duration 60`).
- `--no-chart`: Disable Matplotlib visual chart generation.
- `--no-json`: Disable JSON report generation.

---

## Configuration (`config/config.json`)

```json
{
  "general": {
    "sampling_interval_seconds": 3,
    "report_interval_seconds": 30,
    "history_retention_points": 60,
    "top_process_count": 8
  },
  "thresholds": {
    "cpu_percent": {
      "warning": 75.0,
      "critical": 90.0
    },
    "ram_percent": {
      "warning": 80.0,
      "critical": 92.0
    },
    "swap_percent": {
      "warning": 60.0,
      "critical": 85.0
    },
    "disk_percent": {
      "warning": 85.0,
      "critical": 95.0
    }
  },
  "alerts": {
    "cooldown_seconds": 60,
    "log_alerts_to_console": true
  },
  "paths": {
    "log_file": "logs/monitor.log",
    "reports_dir": "reports"
  },
  "reporting": {
    "generate_json": true,
    "generate_charts": true
  }
}
```

---

## Linux Deployment as a Systemd Service (Optional)

To run the monitor continuously as a background service on Linux:

1. Copy the project folder to `/opt/linux-system-monitor`:
   ```bash
   sudo cp -r . /opt/linux-system-monitor
   ```

2. Copy the service unit to systemd:
   ```bash
   sudo cp system_monitor.service /etc/systemd/system/
   ```

3. Reload systemd and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable system_monitor
   sudo systemctl start system_monitor
   ```

4. Check daemon status and logs:
   ```bash
   sudo systemctl status system_monitor
   sudo journalctl -u system_monitor -f
   ```

---

## Running Automated Tests

Run the complete unit test suite:
- **Windows:**
  ```powershell
  py -3 -m unittest discover tests
  ```
- **Linux:**
  ```bash
  python3 -m unittest discover tests
  ```
