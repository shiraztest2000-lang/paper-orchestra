# SHZ PaperOrchestra Cloud Gateway (initial server component)

This service is the central-cloud option for the Windows desktop client. The
client sends an SHZ account access token; provider API keys stay on the server.

## Current scope

- Authenticated `GET /v1/models` model discovery.
- Authenticated `POST /v1/chat/completions` proxy to one OpenAI-compatible upstream.
- Public `GET /health` health check.
- Hashed user-token verification; raw user tokens are not stored in this service.
- Provider credentials are read only from server environment variables.
- Upstream exception details and secrets are not returned to clients.

This is an initial gateway component, **not a complete public production service**.
It does not yet include self-service registration, password reset, billing,
per-user quotas, usage metering, admin UI, provider failover, streaming, or a
database-backed account/token lifecycle. Add those before opening access to
external users. The current token-hash environment variable is suitable only
for controlled pilot access and must be managed by the server administrator.

## Deploy

1. Copy `.env.example` to `.env` on your own server.
2. Set `SHZ_UPSTREAM_API_KEY` to a provider key owned and funded by you.
3. Create an access token for each pilot user, calculate its SHA-256 digest
   (for example with Python's `hashlib.sha256(token.encode()).hexdigest()`),
   then set `SHZ_GATEWAY_TOKEN_HASHES=user-id:digest`.
4. Set `SHZ_UPSTREAM_BASE_URL` when using an OpenAI-compatible provider other
   than OpenAI.
5. Run `docker compose up -d --build`.
6. Put the service behind HTTPS using a reverse proxy (Caddy, Nginx, or a
   managed load balancer). Do not expose port 8080 directly to the internet.
7. Keep `.env` out of Git and backups/logs that are accessible to clients.

The compose file binds the service to localhost intentionally. Configure TLS
termination and firewall rules on the host. Use a dedicated low-privilege
provider key and configure spending limits with the provider.

## Desktop connection contract

- Base URL: `https://YOUR-HOST/v1`
- Provider: `shz-cloud`
- API key field: an SHZ account access token (not an OpenAI/provider key)
- Model: an ID returned by `GET /v1/models`

The direct-provider option remains separate: in that mode the user supplies
their own provider key to the desktop application. No model weights are
downloaded or installed on Windows in either mode.
