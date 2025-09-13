import os, json
from typing import List
from schemas import TriageResult

try:
    import cohere
except Exception:
    cohere = None

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

SYSTEM = (
    "You are a security triage assistant. "
    "Only use provided log summary and evidence. "
    "Return STRICT JSON matching the schema keys: severity, category, summary, recommended_actions, needs_human_review, confidence, evidence."
)

PROMPT_TEMPLATE = (
    "LOG SUMMARY\n{summary}\n\n"
    "BASELINE SEVERITY: {baseline}\n\n"
    "EVIDENCE (RAG snippets):\n{evidence}\n\n"
    "Now produce JSON with fields: severity (low|medium|high|critical), category, summary, recommended_actions (list of 3-5), needs_human_review (bool), confidence (0-1), evidence (list of short strings)."
)

def _mock_result(summary: str, baseline: str, evidence: List[str]) -> TriageResult:
    sev = "high" if baseline in {"high", "critical"} else "medium"
    category = "auth" if "failed_logins" in summary else ("injection" if "suspicious_paths" in summary else "other")
    return TriageResult(
        severity=sev,
        category=category,
        summary=f"Auto triage: {summary}",
        recommended_actions=[
            "Enforce MFA; lock suspicious accounts",
            "Rate-limit login endpoint; block abusive IP",
            "Rotate keys / revoke tokens; invalidate sessions",
        ],
        needs_human_review=True,
        confidence=0.72,
        evidence=evidence[:3],
    )

def triage_with_llm(summary: str, baseline: str, evidence_snippets: List[str]) -> TriageResult:
    if MOCK_MODE or not (cohere and COHERE_API_KEY):
        return _mock_result(summary, baseline, evidence_snippets)

    co = cohere.Client(COHERE_API_KEY)
    evidence_blob = "\n---\n".join(evidence_snippets)
    prompt = PROMPT_TEMPLATE.format(summary=summary, baseline=baseline, evidence=evidence_blob)

    resp = co.chat(
        model="command-r-plus",
        message=prompt,
        preamble=SYSTEM,
        temperature=0.2,
    )
    text = resp.text.strip()
    data = json.loads(text)
    return TriageResult(**data)
