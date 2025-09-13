import re
from typing import Dict, List

ANOMALY_PATTERNS = {
    "failed_login": re.compile(r"failed login|authentication failed|invalid password", re.I),
    "suspicious_path": re.compile(r"(/admin|/wp-login|/phpmyadmin|union select|\' or 1=1|--)", re.I),
    "server_error": re.compile(r"\b(5\d{2})\b"),
    "llm_prompt_injection": re.compile(r"ignore previous|disregard all|system prompt|leak data", re.I),
}

IP_RE = re.compile(r"(\d{1,3}\.){3}\d{1,3}")

def parse_log(text: str) -> Dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    counts = {k: 0 for k in ANOMALY_PATTERNS}
    ips: List[str] = []
    samples: List[str] = []

    for ln in lines:
        for k, rx in ANOMALY_PATTERNS.items():
            if rx.search(ln):
                counts[k] += 1
                if len(samples) < 8:
                    samples.append(ln[:240])
        ip = IP_RE.search(ln)
        if ip:
            ips.append(ip.group(0))

    top_ip = None
    if ips:
        from collections import Counter
        c = Counter(ips)
        top_ip, _ = c.most_common(1)[0]

    return {
        "line_count": len(lines),
        "counts": counts,
        "top_ip": top_ip,
        "samples": samples,
    }

def baseline_severity(parsed: Dict) -> str:
    c = parsed["counts"]
    if c["llm_prompt_injection"] >= 3 or c["server_error"] >= 25:
        return "critical"
    if c["failed_login"] >= 20 or c["suspicious_path"] >= 10 or c["server_error"] >= 10:
        return "high"
    if any(v >= 3 for v in c.values()):
        return "medium"
    return "low"

def summarize(parsed: Dict) -> str:
    c = parsed["counts"]
    bits = []
    if c["failed_login"]:
        bits.append(f"failed_logins={c['failed_login']}")
    if c["suspicious_path"]:
        bits.append(f"suspicious_paths={c['suspicious_path']}")
    if c["server_error"]:
        bits.append(f"5xx={c['server_error']}")
    if c["llm_prompt_injection"]:
        bits.append(f"llm_injection_signals={c['llm_prompt_injection']}")
    if parsed.get("top_ip"):
        bits.append(f"top_ip={parsed['top_ip']}")
    return ", ".join(bits) or "no obvious anomalies"
