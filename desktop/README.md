# SHZ PaperOrchestra for Windows

The Windows desktop application runs the original PaperOrchestra agents and CLI; it does not simulate the research pipeline.

## Guided first-run setup

On first launch, the Windows app opens a Persian step-by-step setup assistant. It guides the user through choosing a provider, opening the provider's official account/API-key page in the browser, creating and pasting an API key, selecting a model, testing the API connection, and saving settings. The wizard requires a successful connection test before it marks setup complete. It can be reopened at any time from the main window. The app never asks for the provider account password.

## Direct cloud AI — no SHZ server and no local models

This Windows build connects directly from the desktop application to third-party AI providers. It does **not** require an SHZ-owned server, VPS, gateway, Ollama, LM Studio, or downloaded model weights. An internet connection is required.

Supported direct providers:
- **Google Gemini API** (Google AI Studio; some models have a free quota).
- **OpenRouter** (offers free model IDs, including `openrouter/free`).
- **Groq**, **Cerebras**, **DeepSeek**, **Together**, and **OpenAI**.
- A custom HTTPS endpoint implementing the OpenAI-compatible API.

Most providers require the user to create an account and provide their own API key, even when the selected model or usage tier is free. The application does not contain a shared API key and does not silently bill the SHZ project owner. Free access is subject to provider model availability, rate limits, account eligibility, and terms; it is not unlimited or guaranteed.

### Starting with a free option

1. Create a free account with Google AI Studio or OpenRouter.
2. Create an API key in that provider's dashboard.
3. In the app, open **راهنمای گام‌به‌گام اتصال هوش مصنوعی** and select Gemini or OpenRouter.
4. Enter the matching API key in the wizard.
5. For OpenRouter, use a currently available free model ID (usually ending in `:free`) or try `openrouter/free`. Free model availability can change.
6. Run the wizard's connection test. For Gemini, the app retrieves models that advertise `generateContent`; for OpenAI-compatible providers, it queries the provider's `/models` endpoint. The wizard enables saving only after a successful test.

Official provider information:
- Google Gemini API pricing and free tier: https://ai.google.dev/gemini-api/docs/pricing
- Google AI Studio API key setup: https://aistudio.google.com/
- OpenRouter free models: https://openrouter.ai/collections/free-models
- OpenRouter pricing and free-plan limits: https://openrouter.ai/pricing
- Cerebras pricing: https://inference-docs.cerebras.ai/support/pricing

## Credentials and privacy

Provider API keys are stored in the current Windows user's Windows Credential Manager through the OS credential store. Non-secret preferences remain in `%APPDATA%/SHZ PaperOrchestra/.env`. Existing API keys found in a legacy plaintext `.env` file are migrated into the credential store at startup and removed from that file after successful migration. If secure storage is unavailable, the app refuses to save credentials as plaintext. Use provider-side spending/rate limits where available. The app does not include an SHZ central-gateway sign-in mode in this direct-cloud build.

## Literature discovery

Candidate discovery uses OpenAlex and Crossref. Candidate records are subsequently enriched through the existing Semantic Scholar integration. Internet access is required for scholarly discovery and metadata enrichment. A Semantic Scholar API key may be needed for higher or sustained request volume.

## Run and build

- Windows x64; Python 3.11 for development.
- Install: `pip install -r requirements.txt -r desktop/requirements.txt`.
- Run: `python desktop_app.py` from the repository root.
- Projects are saved in `Documents/SHZ PaperOrchestra/Projects`.
- The Windows workflow builds an Inno Setup installer.
- A local TeX distribution may be required to compile the final PDF.
- The upstream dataset is not included; the app does not invent it.

## Compatibility note

The application uses Gemini's native integration and OpenAI-compatible chat completions for the other listed providers. Validate each selected model against the full research workflow before relying on it: structured JSON output, long-context handling, PDF/image input, and plotting-agent compatibility can vary by provider/model. The desktop connection test checks configuration/model discovery; it does not guarantee every agent capability.
