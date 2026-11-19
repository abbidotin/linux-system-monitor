
# Linux System Health Monitor

A Bash-based utility that collects basic Linux system information,
monitors resource usage, and generates timestamped reports.

## Features

- Operating system and kernel information
- System uptime
- Memory usage and warning threshold
- Root filesystem usage and warning threshold
- CPU load averages
- Logged-in users
- Top processes by CPU usage
- Network interfaces
- Listening TCP ports
- Timestamped text reports

## Requirements

- Ubuntu or a compatible Linux distribution
- Bash
- Standard Linux utilities: free, df, ps, ip, ss, who, tee

## Installation

Clone the repository:

    git clone https://github.com/YOUR_USERNAME/linux-system-monitor.git

Enter the directory:

    cd linux-system-monitor

Make the script executable:

    chmod +x system-monitor.sh

## Usage

Run:

    ./system-monitor.sh

The report is saved in the reports/ directory.

## Learning Objectives

- Bash scripting
- Linux system information
- Process inspection
- Resource monitoring
- Networking commands
- File handling and logging
- Git and GitHub

## Limitations

This is an educational monitoring utility.
It does not provide continuous monitoring, historical
trend analysis, or production-grade alerting.

## Future Improvements

- Configurable warning thresholds
- JSON report output
- Automated scheduled reports
- Email or webhook alerts
- Unit tests
