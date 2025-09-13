import os
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from triage import parse_log, baseline_severity, summarize
from rag import search, build_index
from llm import triage_with_llm
from blockkit import triage_blocks
from slack_sdk.web import WebClient

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")
INGEST_SECRET = os.getenv("INGEST_SECRET")

client = WebClient(token=SLACK_BOT_TOKEN)
api = FastAPI(title="Triageo Ingest")

class SiemEvent(BaseModel):
    source: str | None = None
    severity: str | None = None
    rule: str | None = None
    message: str | None = None
    raw: dict | None = None
    lines: list[str] | None = None

def triage_text_to_slack(text: str, channel: str | None = None):
    build_index()
    parsed = parse_log(text)
    base = baseline_severity(parsed)
    summary = summarize(parsed)
    ev = [d["text"] for d in search(summary, k=3)]
    result = triage_with_llm(summary=summary, baseline=base, evidence_snippets=ev)
    blocks = triage_blocks(result)
    client.chat_postMessage(channel=channel or SLACK_CHANNEL_ID, blocks=blocks)

@api.post("/ingest/siem")
async def ingest(req: Request):
    # Optional shared-secret check
    if INGEST_SECRET and req.headers.get("X-Triageo-Secret") != INGEST_SECRET:
        return Response(status_code=401)

    try:
        body = await req.json()
    except Exception:
        body = {}
    evt = SiemEvent(**body)

    if evt.lines:
        text = "\n".join(evt.lines)
    elif evt.message:
        text = evt.message
    elif evt.raw:
        text = str(evt.raw.get("message") or evt.raw.get("log") or evt.raw)
    else:
        text = str(body)

    triage_text_to_slack(text=text, channel=os.getenv("SLACK_CHANNEL_ID"))
    return {"ok": True}
