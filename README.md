# Zopi Guard 🛡️

A modern desktop application that protects your Windows RDP server from brute-force login attacks. Monitors the Windows Security Event Log and automatically blocks offending IPs via Windows Firewall.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## Features

- **Real-time monitoring** of Windows Security Event Log (Event ID 4625)
- **Automatic blocking** — temporary (configurable) and permanent blocks
- **Modern dark GUI** built with PyQt6
- **Live dashboard** with attempt chart and event log
- **Username tracking** — see which accounts are being targeted
- **Email alerts** on permanent blocks
- **System tray** — runs silently in the background
- **Auto-start** with Windows
- **Auto-updater** — checks GitHub for new releases

---

## Requirements

- Windows Server or Windows 10/11
- Python 3.11+
- Administrator privileges

---

## Installation

```bash
pip install -r requirements.txt
python main.py
```

> Must be run as Administrator for firewall management and event log access.

---

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run as Administrator: `python main.py`
3. Go to **Settings** and add your own IP to the whitelist
4. Click **▶ START** to begin monitoring

---

## Built by [Zopi Ltd](https://zopi.uk)
