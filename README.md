# System Health Monitor 🖥️

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Bash](https://img.shields.io/badge/Bash-GNU-green.svg?logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg)](https://github.com/abbidotin/system-health-monitor)
[![Version](https://img.shields.io/badge/Release-v2.0.0-brightgreen.svg)](https://github.com/abbidotin/system-health-monitor/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A modular, cross-platform system monitoring suite designed to track hardware metrics, enforce threshold-based alerts, and produce automated performance reports.

This repository hosts two distinct editions tailored for different operational needs:
1. **[Version 2.0 (Python Edition)](./v2-python/)** — Advanced, cross-platform telemetry agent with real-time terminal watch, intelligent threshold alerts, and multi-panel Matplotlib visual analytics for Linux and Windows.
2. **[Version 1.0 (Bash Edition)](./v1-bash/)** — Minimalist, zero-dependency shell script engineered for lightweight Linux servers, embedded systems, and containers.

---

## 🚀 What's New in Version 2.0

| Feature | Version 1.0 (Bash Edition) | Version 2.0 (Python Edition) |
| :--- | :--- | :--- |
| **Supported OS** | Linux only | **Linux & Windows** |
| **Tech Stack** | Pure Bash / GNU coreutils | Python 3, `psutil`, `matplotlib`, `logging` |
| **Visual Charts** | None (text output only) | **4-Panel Matplotlib PNG Performance Graphs** |
| **Threshold Alerts** | Basic log messages | **Warning/Critical levels with cooldown & auto-recovery** |
| **Reporting** | Plain text files | **Structured JSON snapshots + Visual PNG charts** |
| **Operational Modes** | Single script execution | **`snapshot`, interactive live `watch`, background `daemon`** |
| **Testing** | Manual testing | **14 Automated Unit Tests (`unittest`)** |
| **Background Service** | Cron job | **Native Linux `systemd` service integration** |

---

## 📁 Repository Structure

```text
system-health-monitor/
├── README.md                      # Main repository documentation & guide
│
├── v1-bash/                       # Version 1.0: Zero-dependency Linux shell monitor
│   ├── monitor.sh                 # Core Bash script
│   └── README.md                  # Bash setup and usage documentation
│
└── v2-python/                     # Version 2.0: Cross-platform Python monitoring agent
    ├── config/
    │   └── config.json            # Thresholds, intervals, and paths configuration
    ├── monitor/
    │   ├── __init__.py            # Package exports
    │   ├── cpu.py                 # CPU %, cores, frequency, load average
    │   ├── memory.py              # RAM, swap, buffers, and cache metrics
    │   ├── disk.py                # Disk capacity, partition filtering, I/O rates
    │   ├── network.py             # Interface stats, error counts, bandwidth speed
    │   ├── process.py             # Process analyzer and resource ranking
    │   ├── alerts.py              # Threshold evaluator, cooldown, and recovery engine
    │   ├── reporter.py            # JSON report generator and Matplotlib visualizer
    │   └── engine.py              # Central monitoring orchestrator
    ├── reports/                   # Output directory for JSON summaries and PNG charts
    ├── logs/                      # Output directory for alert logs
    ├── tests/                     # Automated unit test suite (14 test cases)
    ├── main.py                    # Main CLI application (snapshot, watch, daemon)
    ├── run_monitor.bat            # 1-Click launcher for Windows
    ├── run_monitor.sh             # 1-Click launcher for Linux
    ├── system_monitor.service     # Linux systemd daemon service unit
    ├── requirements.txt           # Python dependencies
    └── README.md                  # Comprehensive Python documentation
```

---

## ⚡ Quickstart

### Option A: Running Version 2.0 (Python Edition — Recommended)

The Python edition runs on both **Windows** and **Linux**.

1. Navigate to the Python directory and install dependencies:
   ```bash
   cd v2-python
   pip install -r requirements.txt
   ```

2. Choose your operating mode:
   * **Instant Diagnostic Snapshot** (Terminal summary + JSON & PNG chart):
     * *Windows:* `py -3 main.py snapshot`
     * *Linux:* `python3 main.py snapshot`
   * **Interactive Live Dashboard** (Updates every 3s in terminal):
     * *Windows:* `py -3 main.py watch`
     * *Linux:* `python3 main.py watch`
   * **Continuous Background Daemon** (Alerts to log + periodic reports):
     * *Windows:* `py -3 main.py daemon`
     * *Linux:* `python3 main.py daemon`

👉 **[Read the complete Version 2.0 Documentation](./v2-python/README.md)** for detailed configuration, testing, and Linux systemd deployment.

---

### Option B: Running Version 1.0 (Bash Edition)

The original zero-dependency utility for minimal Linux environments.

1. Navigate to the Bash directory:
   ```bash
   cd v1-bash
   ```

2. Make executable and run:
   ```bash
   chmod +x monitor.sh
   ./monitor.sh
   ```

👉 **[Read the Version 1.0 Documentation](./v1-bash/README.md)** for cron automation and script parameters.

---

## 🧪 Testing

Version 2.0 includes a comprehensive unit test suite covering metric collection, threshold evaluation, and report generation:

```bash
cd v2-python
python3 -m unittest discover tests
```

---

## 👤 Author

**Abhinav**
- GitHub: [@abbidotin](https://github.com/abbidotin)

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
