
#!/usr/bin/env bash

set -u

# Linux System Health Monitor
# Tested for Bash on Ubuntu

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$SCRIPT_DIR/reports"
TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
REPORT_FILE="$REPORT_DIR/report-$TIMESTAMP.txt"

mkdir -p "$REPORT_DIR" || {
    echo "Error: Cannot create reports directory." >&2
    exit 1
}

# Display output on screen and save it to a report.
exec > >(tee "$REPORT_FILE") 2>&1

echo "========================================"
echo "       LINUX SYSTEM HEALTH MONITOR"
echo "========================================"
echo "Generated: $(date)"
echo

# Operating system
echo "[ SYSTEM INFORMATION ]"
if [[ -r /etc/os-release ]]; then
    . /etc/os-release
    echo "OS: ${PRETTY_NAME:-Unknown}"
fi
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Uptime: $(uptime -p 2>/dev/null || uptime)"
echo

# Memory usage
echo "[ MEMORY USAGE ]"
if command -v free >/dev/null 2>&1; then
    free -h
    MEMORY_PERCENT="$(free -b | awk '/^Mem:/ {
        if ($2 > 0) printf "%.0f", ($3 / $2) * 100;
        else print 0
    }')"

    echo "Memory used: ${MEMORY_PERCENT}%"

    if (( MEMORY_PERCENT >= 85 )); then
        echo "WARNING: High memory usage."
    else
        echo "STATUS: Memory usage within threshold."
    fi
else
    echo "Memory utility 'free' is unavailable."
fi
echo

# Disk usage
echo "[ ROOT FILESYSTEM ]"
DISK_PERCENT="$(df -P / | awk 'NR == 2 {
    gsub(/%/, "", $5);
    print $5
}')"

df -h /

if [[ "$DISK_PERCENT" =~ ^[0-9]+$ ]]; then
    if (( DISK_PERCENT >= 85 )); then
        echo "WARNING: Root filesystem usage is high."
    else
        echo "STATUS: Root filesystem usage within threshold."
    fi
else
    echo "WARNING: Could not determine disk usage."
fi
echo

# CPU load
echo "[ CPU LOAD ]"
if [[ -r /proc/loadavg ]]; then
    read -r LOAD_1 LOAD_5 LOAD_15 _ < /proc/loadavg
    echo "1-minute load average: $LOAD_1"
    echo "5-minute load average: $LOAD_5"
    echo "15-minute load average: $LOAD_15"
    echo "Note: Load average is not CPU usage percentage."
fi
echo

# Logged-in users
echo "[ LOGGED-IN USERS ]"
who
echo

# Top processes
echo "[ TOP PROCESSES BY CPU ]"
ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n 6
echo

# Network interfaces
echo "[ NETWORK INTERFACES ]"
if command -v ip >/dev/null 2>&1; then
    ip -brief address
else
    echo "The 'ip' command is unavailable."
fi
echo

# Listening sockets
echo "[ LISTENING PORTS ]"
if command -v ss >/dev/null 2>&1; then
    ss -lnt
else
    echo "The 'ss' command is unavailable."
fi
echo

echo "========================================"
echo "Report saved to: $REPORT_FILE"
echo "System health check completed."
echo "========================================"
