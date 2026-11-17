# SHZ PaperOrchestra for Windows

The Windows desktop application runs the original PaperOrchestra agents and CLI; it does not simulate the research pipeline.

## Cloud-only AI providers

No AI model weights are downloaded or installed on the Windows PC. All language-model inference is performed over the internet.

Two connection modes are available:

1. **SHZ Cloud (central gateway):** the server administrator operates the gateway and pays the upstream provider bill. The desktop client uses an SHZ account access token; the provider API key remains on the server.
2. **Direct provider connection:** the user selects a cloud provider and enters their own provider API key. Supported OpenAI-compatible hosted providers include OpenAI, OpenRouter, DeepSeek, Groq, Together, and custom hosted endpoints. Gemini and Vertex AI remain supported through their existing integration.

Local model endpoints (Ollama and LM Studio) are disabled in this Windows build. An internet connection is required.

Use Settings → AI connection to select the provider, configure the cloud endpoint or direct provider key, test the connection, and discover compatible models. The SHZ Cloud endpoint should be the gateway's HTTPS base URL ending in `/v1`. The account token is not a provider API key.

Direct-provider credentials and the SHZ account token are stored in the current Windows user's `%APPDATA%/SHZ PaperOrchestra/.env`; do not commit or share this file. The gateway's provider credentials must be stored only in the server's environment, never in the desktop executable or repository.

## Central gateway

The initial FastAPI/Docker gateway is in `cloud_gateway/`. See [cloud_gateway/README.md](../cloud_gateway/README.md) for deployment and its current limitations. The first version supports authenticated model discovery and non-streaming chat completions through one OpenAI-compatible upstream. It is not yet a full account-registration, billing, quota, or admin platform.

## Literature discovery

Candidate discovery uses OpenAlex and Crossref. Candidate records are subsequently enriched through the existing Semantic Scholar integration. Internet access is required for scholarly discovery and metadata enrichment.

## Run and build

- Windows x64; Python 3.11 for development.
- Install: `pip install -r requirements.txt -r desktop/requirements.txt`.
- Run: `python desktop_app.py` from the repository root.
- Projects are saved in `Documents/SHZ PaperOrchestra/Projects`.
- The Windows workflow builds an Inno Setup installer.
- A local TeX distribution may be required to compile the final PDF.
- The upstream dataset is not included; the app does not invent it.

## Compatibility note

The central gateway currently proxies text chat completions and model discovery. Validate image/PDF workloads and optional vendor-specific upstream features before production use. Some upstream agents may still rely on provider-specific capabilities; cloud-only compatibility must be tested end-to-end for each selected model.
