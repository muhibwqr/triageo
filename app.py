import os, requests
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from triage import parse_log, baseline_severity, summarize
from rag import search, build_index
from llm import triage_with_llm
from blockkit import triage_blocks

load_dotenv()
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("app_mention")
def on_mention(body, say, logger):
    print("DEBUG: Received app_mention event!")
    logger.info(f"Full event payload: {body}")

    text = body.get("event", {}).get("text", "")
    files = body.get("event", {}).get("files", [])

    print(f"DEBUG: Text content: {text}")
    print(f"DEBUG: Files detected: {files}")

    if files:
        try:
            f = files[0]
            url = f.get("url_private_download")
            headers = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            content = r.text
            print("DEBUG: File content fetched")
            say("⏳ Triage in progress…")
            _process_and_reply(say, content)
            return
        except Exception as e:
            logger.exception(e)
            say(f"Could not read file: {e}")
            return

    lower = text.lower()
    if "log" in lower:
        payload = text.split("log", 1)[-1]
        if payload.strip():
            print("DEBUG: Log detected in mention")
            say("⏳ Triage in progress…")
            _process_and_reply(say, payload)
            return

    print("DEBUG: No actionable content detected")
    say("Triageo here. Upload a file and @mention me, or @mention me with the word `log` followed by pasted lines.")

@app.action("btn_escalate")
def on_escalate(ack, body, client, logger):
    ack()
    client.chat_postMessage(channel=body["channel"].get("id"), text="🚨 Escalation noted. Paging on‑call (demo mode).")

@app.action("btn_ack")
def on_ack(ack, body, client):
    ack()
    client.chat_postMessage(channel=body["channel"].get("id"), text="👀 Acknowledged by human. Logging to audit trail (demo mode).")

@app.action("btn_lower")
def on_lower(ack, body, client):
    ack()
    client.chat_postMessage(channel=body["channel"].get("id"), text="⬇️ Severity lowered (demo mode).")

@app.action("btn_why")
def on_why(ack, body, client):
    ack()
    client.chat_postMessage(channel=body["channel"].get("id"), text="🧠 Why: baseline signals + OWASP snippets informed this severity (demo mode).")

def _process_and_reply(respond_fn, text: str):
    build_index()
    parsed = parse_log(text)
    base = baseline_severity(parsed)
    summary = summarize(parsed)
    ev = [d["text"] for d in search(summary, k=3)]
    result = triage_with_llm(summary=summary, baseline=base, evidence_snippets=ev)
    blocks = triage_blocks(result)
    respond_fn(blocks=blocks)

if __name__ == "__main__":
    app_token = os.getenv("SLACK_APP_TOKEN")
    if not app_token:
        raise SystemExit("Missing SLACK_APP_TOKEN in .env")
    SocketModeHandler(app, app_token).start()
