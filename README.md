# triageo
ai agent taking security chaos to clarity - built for hack the north 2025
# Triageo

**Slack-native AI Security Triage Bot**

Triageo ingests logs and system docs, triages incidents, and suggests threat-aware responses — all inside Slack. Built for **Hack the North 2025**.

## Features
- 🔎 Incident Triage
- 🛡️ Security Grounding (OWASP Top-10 + runbooks)
- 🤖 Threat Modeling
- 💬 Slack-native UX
- 🧑‍💻 Human-in-the-loop

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
