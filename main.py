import threading, os
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from app import app as bolt_app
import uvicorn

load_dotenv()

def demo_blocks(tr):
    SEV_EMOJI = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }
    sev = tr.severity
    emoji = SEV_EMOJI.get(sev, "❗")
    actions = "\n".join([f"• {a}" for a in tr.recommended_actions])
    ev = "\n".join([f"– {e}" for e in tr.evidence]) or "(no evidence)"
    header = f"{emoji} TRIAGEO – {sev.upper()} (conf {tr.confidence:.2f})"

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": header}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Category:* `{tr.category}`\n*Summary:* {tr.summary}"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Recommended actions:*\n{actions}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Evidence:*\n{ev}"}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "🚨 Escalate"}, "value": "escalate"},
            {"type": "button", "text": {"type": "plain_text", "text": "👀 Acknowledge"}, "value": "ack"},
            {"type": "button", "text": {"type": "plain_text", "text": "⬇️ Lower severity"}, "value": "lower"},
        ]},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Needs human review: *{str(tr.needs_human_review).lower()}*"}]},
    ]
    return blocks

def run_slack():
    SocketModeHandler(bolt_app, os.getenv("SLACK_APP_TOKEN")).start()

def run_http():
    uvicorn.run("server:api", host="0.0.0.0", port=8080, reload=False)

if __name__ == "__main__":
    t1 = threading.Thread(target=run_slack, daemon=True)
    t1.start()
    run_http()
