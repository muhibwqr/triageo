import json, os
from typing import List, Dict, Tuple
import numpy as np

try:
    import cohere
except Exception:
    cohere = None

INDEX_PATH = os.getenv("INDEX_PATH", ".kb_index.json")
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "cohere")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

def _embed_texts(texts: List[str]) -> np.ndarray:
    if EMBED_PROVIDER == "cohere" and cohere and COHERE_API_KEY:
        co = cohere.Client(COHERE_API_KEY)
        resp = co.embed(texts=texts, model="embed-english-v3.0")
        return np.array(resp.embeddings, dtype="float32")
    rng = np.random.default_rng(0)
    return rng.normal(size=(len(texts), 384)).astype("float32")

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)

def build_index() -> None:
    docs = []
    kb_files = ["kb/owasp_llm_top10.md", "kb/runbooks.md"]
    for fp in kb_files:
        if not os.path.exists(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = [t.strip() for t in text.split("\n\n") if t.strip()]
        for ch in chunks:
            docs.append({"text": ch})
    if not docs:
        docs = [{"text": "OWASP LLM Top10: Prompt Injection, Data Exfiltration, Insecure Output Handling, Over-permissioned Tools, Data Poisoning, SSRF via tools, etc."}]

    embs = _embed_texts([d["text"] for d in docs])
    for d, e in zip(docs, embs):
        d["vec"] = e.tolist()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump({"docs": docs}, f)

def search(query: str, k: int = 3) -> List[Dict]:
    if not os.path.exists(INDEX_PATH):
        build_index()
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        idx = json.load(f)
    docs = idx.get("docs", [])
    qv = _embed_texts([query])[0]
    scored: List[Tuple[float, Dict]] = []
    for d in docs:
        import numpy as np
        v = np.array(d["vec"], dtype="float32")
        denom = (np.linalg.norm(qv) * np.linalg.norm(v)) or 1.0
        score = float(np.dot(qv, v) / denom)
        scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:k]]
