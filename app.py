# app.py — Triageo (Demo-mode guaranteed cards)

import os, re, requests, threading, time
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web import WebClient

# ---- Local modules (used when DEMO_MODE=false) ----
try:
    from triage import parse_log, baseline_severity, summarize
    from rag import search, build_index
    from llm import triage_with_llm
    from blockkit import triage_blocks
except Exception:
    # OK in demo mode; we’ll build cards manually.
    parse_log = baseline_severity = summarize = search = build_index = triage_with_llm = triage_blocks = None

# ============ ENV ============
load_dotenv()
BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
DEFAULT_CHANNEL = os.getenv("SLACK_CHANNEL_ID")  # optional (for realtime tail)
DEMO_MODE = (os.getenv("DEMO_MODE", "true").lower() == "true")

if not BOT_TOKEN:
    raise SystemExit("Missing SLACK_BOT_TOKEN in .env")
if not APP_TOKEN:
    raise SystemExit("Missing SLACK_APP_TOKEN in .env")

app = App(token=BOT_TOKEN)
client = WebClient(token=BOT_TOKEN)

# ============ Simple heuristics for demo ============
IP_RE = re.compile(r"(\d{1,3}\.){3}\d{1,3}")
def quick_detect(text: str):
    lower = text.lower()
    sev = "low"
    cat = "other"
    actions = ["Review logs"]

    if "login failed" in lower or "failed login" in lower:
        sev = "high"; cat = "auth"
        actions = ["Block abusive IP", "Enable MFA", "Review IAM events"]
    if "union select" in lower or " or 1=1" in lower or "injection" in lower:
        sev = "critical"; cat = "injection"
        actions = ["Block source IP", "Sanitize inputs", "Review DB logs"]
    ip = IP_RE.search(text)
    return {
        "severity": sev,
        "category": cat,
        "summary": f"Detected {cat} pattern" if cat != "other" else "Log anomaly",
        "evidence": [ip.group(0)] if ip else [],
        "actions": actions,
        "confidence": 0.9 if sev in ("high", "critical") else 0.6,
    }

def demo_blocks(text: str):
    d = quick_detect(text or "")
    sev_emoji = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢"}.get(d["severity"], "❗")
    header = f"{sev_emoji} TRIAGEO – {d['severity'].upper()} (conf {d['confidence']:.2f})"
    ev = (", ".join(d["evidence"])) if d["evidence"] else "n/a"
    return [
        {"type": "header", "text": {"type": "plain_text", "text": header}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Category:* `{d['category']}`\n*Summary:* {d['summary']}"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Recommended actions:*\n" + "\n".join("• "+a for a in d["actions"])}},
        {"type": "context", "elements": [{"type":"mrkdwn","text": f"*Evidence:* {ev}"}]},
        {"type": "actions", "elements": [
            {"type":"button","text":{"type":"plain_text","text":"🚨 Escalate"},"value":"escalate","action_id":"btn_escalate"},
            {"type":"button","text":{"type":"plain_text","text":"👀 Acknowledge"},"value":"ack","action_id":"btn_ack"},
            {"type":"button","text":{"type":"plain_text","text":"⬇️ Lower severity"},"value":"lower","action_id":"btn_lower"},
        ]},
    ]

# ============ Card builder ============
def build_blocks_from_text(text: str):
    if DEMO_MODE or not all([parse_log, baseline_severity, summarize, search, build_index, triage_with_llm, triage_blocks]):
        return demo_blocks(text)

    # Real pipeline
    try:
        build_index()
        parsed = parse_log(text)
        base = baseline_severity(parsed)
        summary = summarize(parsed)
        ev = [d["text"] for d in search(summary, k=3)]
        result = triage_with_llm(summary=summary, baseline=base, evidence_snippets=ev)
        blocks = triage_blocks(result)
        if not blocks:
            raise ValueError("triage_blocks returned empty")
        return blocks
    except Exception as e:
        print("⚠️ AI pipeline failed, falling back to demo:", repr(e))
        return demo_blocks(text)

def post_card(channel_id: str, blocks):
    try:
        resp = client.chat_postMessage(channel=channel_id, text="🔔 Triageo alert", blocks=blocks)
        thread_ts = resp.get("ts")
        # Optional: attach an image thread if you have pick_random_image()
        try:
            from images import pick_random_image
            img = pick_random_image()
            if img and thread_ts:
                client.files_upload_v2(
                    channel=channel_id,
                    file=img,
                    filename=os.path.basename(img),
                    initial_comment="🎲 Random asset attached",
                    thread_ts=thread_ts,
                )
        except Exception as e:
            print("Image attach failed:", repr(e))
    except Exception as e:
        print("chat_postMessage failed:", repr(e))
        try:
            client.chat_postMessage(channel=channel_id, text="⚠️ Could not render triage card.")
        except Exception as ee:
            print("Fallback text post failed:", repr(ee))

# ============ Slack events ============
@app.event("app_mention")
def on_mention(body, say, logger):
    event = body.get("event", {}) or {}
    channel_id = event.get("channel")
    text = (event.get("text") or "").strip()
    files = event.get("files") or []

    try:
        say("⏳ Triage in progress…")
    except Exception as e:
        print("say() failed:", repr(e))

    try:
        # 1) file upload path
        if files:
            f = files[0]
            url = f.get("url_private_download")
            headers = {"Authorization": f"Bearer {BOT_TOKEN}"}
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            content = r.text
            post_card(channel_id, build_blocks_from_text(content)); return

        # 2) inline after "log"
        lower = text.lower()
        payload = text.split("log", 1)[-1].strip() if "log" in lower else text
        if payload:
            post_card(channel_id, build_blocks_from_text(payload)); return

        # 3) nudge
        post_card(channel_id, demo_blocks("Send `@Triageo log <lines>` or upload a file."))

    except Exception as e:
        logger.exception(e)
        try:
            client.chat_postMessage(channel=channel_id, text="⚠️ Could not build the triage card (exception logged).")
        except Exception as ee:
            print("Final nudge failed:", repr(ee))

@app.action("btn_escalate")
def on_escalate(ack, body, client, logger):
    ack(); client.chat_postMessage(channel=body["channel"]["id"], text="🚨 Escalation noted (demo).")

@app.action("btn_ack")
def on_ack(ack, body, client):
    ack(); client.chat_postMessage(channel=body["channel"]["id"], text="👀 Acknowledged (demo).")

@app.action("btn_lower")
def on_lower(ack, body, client):
    ack(); client.chat_postMessage(channel=body["channel"]["id"], text="⬇️ Severity lowered (demo).")

# ============ Realtime tail (optional) ============
LOG_FILE = "samples/auth_burst.log"
def tail_log(path):
    P = Path(path); P.parent.mkdir(parents=True, exist_ok=True); P.touch(exist_ok=True)
    with open(path, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line: time.sleep(0.5); continue
            yield line.strip()

def start_realtime():
    if not DEFAULT_CHANNEL:
        print("⏭️ Realtime disabled (set SLACK_CHANNEL_ID to enable)."); return
    print(f"📡 Tailing {LOG_FILE} → {DEFAULT_CHANNEL}")
    for line in tail_log(LOG_FILE):
        try:
            post_card(DEFAULT_CHANNEL, build_blocks_from_text(line))
        except Exception as e:
            print("Realtime failed:", repr(e))

threading.Thread(target=start_realtime, daemon=True).start()

# ============ Entrypoint ============
if __name__ == "__main__":
    SocketModeHandler(app, APP_TOKEN).start()
