# Payment Service – Quick Overview
- Frontend → API Gateway → Payment Service (Node) → DB (Postgres)
- Auth via OAuth2; Webhook listener for provider callbacks
- Secrets in AWS Secrets Manager
- Outbound calls to 3rd‑party Payment Provider
