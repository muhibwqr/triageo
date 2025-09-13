# OWASP LLM Top 10 (Mini Cheat Sheet)

- Prompt Injection & Jailbreaks → Validate/ground inputs; never execute raw tool calls from untrusted prompts.
- Data Leakage & Sensitive Info Exposure → Redact logs; scope data; avoid echoing secrets.
- Insecure Output Handling → Sanitize model outputs before using in code/tools.
- Over‑permissioned Tools/Agents → Least privilege; approval gates for destructive actions.
- Training/Prompt Data Poisoning → Verify sources; integrity checks.
- Supply Chain of Models/Plugins → Verify signatures; pin versions.
- Model Denial of Service (Token floods) → Rate limits & size caps.
- SSRF via Tools/Functions → Restrict egress; allow‑lists for URLs/hosts.
- Secrets in Prompts/Context → Use KMS/secret managers; never inline secrets.
- Toxic/Unsafe Content → Safety filters; policy prompts; human-in-the-loop.
