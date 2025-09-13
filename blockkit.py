from typing import List
from schemas import TriageResult

SEV_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

def triage_blocks(tr: TriageResult) -> List[dict]:
    sev = tr.severity
    emoji = SEV_EMOJI.get(sev, "❗")
    actions = "\n".join([f"• {a}" for a in tr.recommended_actions])
    ev = "\n".join([f"– {e}" for e in tr.evidence]) or "(no evidence)"
    header = f"{emoji} *Triageo – {sev.upper()}* (conf {tr.confidence:.2f})"

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": header}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Category:* `{tr.category}`\n*Summary:* {tr.summary}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Recommended actions:*\n{actions}"}},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*Evidence:*\n{ev}"}]},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "🚨 Escalate"}, "value": "escalate", "action_id": "btn_escalate"},
            {"type": "button", "text": {"type": "plain_text", "text": "👀 Acknowledge"}, "value": "ack", "action_id": "btn_ack"},
            {"type": "button", "text": {"type": "plain_text", "text": "⬇️ Lower severity"}, "value": "lower", "action_id": "btn_lower"},
            {"type": "button", "text": {"type": "plain_text", "text": "❓ Why?"}, "value": "why", "action_id": "btn_why"},
        ]},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Needs human review: *{str(tr.needs_human_review).lower()}*"}]},
    ]
    return blocks
