# Trinetra — Broken Access Finder 🚀

A multi-threaded web vulnerability scanner built with Python and CustomTkinter. Automates the detection of broken links and identifies potential Broken Access Control (BAC/IDOR) endpoints.

## Overview
In the world of web security, Broken Access Control (BAC) is consistently ranked as a top vulnerability. Trinetra (Sanskrit for "Third Eye") acts as an automated observer, crawling your target web application to uncover hidden risks that manual browsing might miss.

It recursively scans a domain, identifies broken resources (404s), and uses heuristic patterns to flag endpoints potentially vulnerable to IDOR (Insecure Direct Object References) and privilege escalation.

## ✨ Key Features
- 🕷️ Smart Crawling: Recursively maps website structure to a user-defined depth.
- 🚫 Broken Link Detector: Instantly flags 4xx and 5xx errors to help maintain site hygiene and prevent subdomain takeovers.
- 🔓 IDOR & BAC Discovery: Intelligently hunts for sensitive keywords (e.g., `admin`, `config`) and suspicious parameter patterns (`?id=123`, `user_id=`) that often indicate access control flaws.
- 🖥️ Modern GUI: Built with CustomTkinter for a sleek, dark-mode compatible interface.
- ⚡ Multi-threaded: Keeps the UI responsive while performing heavy network operations in the background.

## 🛠️ Installation & Usage
Bash

```bash
# Clone the repository
git clone https://github.com/TirupMehta/BrokenAccessFinder.git

# Install dependencies
pip install -r requirements.txt

# Run the scanner
python main.py
```

## ⚠️ Disclaimer
This tool is intended for educational purposes and security research only. Ensure you have proper authorization before scanning any domain.
