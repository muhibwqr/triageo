# Triageo

**Slack-native AI Security Triage Bot**

Triageo ingests logs and system docs, triages incidents, and suggests threat-aware responses — all inside Slack. Built for **Hack the North 2025**.

---

## 🎯 Why We Built Triageo
Security engineers and developers are overwhelmed by **noisy alerts, logs, and incidents**. Threat modeling is often skipped because it’s slow and manual. We asked: can an **AI agent** cut through the noise, ground its reasoning in trusted security knowledge, and suggest the *right first steps* — directly in Slack?

Triageo is our answer: a **Slack-first triage assistant** that blends lightweight heuristics, retrieval‑augmented AI, and a human‑in‑the‑loop flow.

---

## 🛠️ Tech Stack
- **Languages**: Python 3.11
- **Slack**: Bolt (Python), Socket Mode (no public URL required)
- **AI & RAG**: Cohere Embed v3 for embeddings; Cohere/Bedrock LLM for reasoning; tiny JSON index (FAISS-like behavior)
- **Data**: Local JSON/SQLite (optional) for audit trail
- **Security Content**: OWASP LLM Top‑10 + mini runbooks

---

## 🚀 Features
- 🔎 **Incident triage**: log parsing, anomaly detection, severity classification
- 🛡️ **Security grounding**: RAG over OWASP LLM Top‑10 + runbooks
- 🤖 **Threat modeling**: upload system docs → top risks + mitigations
- 💬 **Slack‑native UX**: emoji severity badges, action buttons, human‑in‑the‑loop
- 🧑‍💻 **Hackathon‑ready**: Mock mode (no external API needed) with easy switch to live LLM

---

## ⚡ Quickstart
1. **Create Slack App** (https://api.slack.com/apps)
   - *Socket Mode*: **On**
   - *App‑level token*: create with `connections:write` → **SLACK_APP_TOKEN** (`xapp-…`)
   - *Bot Scopes*: `app_mentions:read`, `chat:write`, `files:read`, `channels:history`, `im:history` → Install → **SLACK_BOT_TOKEN** (`xoxb-…`)
2. **Install deps & run**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env  # fill tokens & keys
   python app.py
   ```
3. **Try it in Slack**
   - Mention the bot and say: `log` then paste a few lines, **or** upload `samples/auth_burst.log` and mention @Triageo in the thread.

---

## 🧪 Demo Script (5 min)
1. Upload `samples/auth_burst.log` and @mention the bot → triage card (HIGH severity).
2. Click **Escalate** → explain human‑in‑the‑loop.
3. Paste `samples/injection_trace.log` in a mention → category switches to `injection`.
4. (Stretch) Upload `samples/system.md` and @mention `threatmodel` → top‑5 risks.

---

## Supported Input Formats
- **Pasted logs** in a mention (`@Triageo log ...`)
- **File uploads**: `.log`, `.txt` (mention the bot in the thread)
- **System docs**: `.md` for threat-sweep
- **Webhook JSON** (optional): `{ lines:[], message, raw }` to `/ingest/siem`

---

## 🧭 Roadmap
- Persist button actions (ack/escalate) to `state.json` or SQLite
- On‑call mapping (service → Slack group)
- Cloud log connectors (AWS/GCP/Datadog)
- Compliance helpers (SOC2 style report drafts)

---

## 📜 License
MIT (hackathon demo)
