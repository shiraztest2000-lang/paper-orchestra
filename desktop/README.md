# SHZ PaperOrchestra for Windows

The Windows desktop application runs the original PaperOrchestra agents and CLI; it does not simulate the research pipeline.

## LLM providers

- Gemini and Vertex AI remain supported.
- OpenAI-compatible endpoints are supported through the shared provider adapter.
- Local endpoints: Ollama at `http://127.0.0.1:11434/v1` and LM Studio at `http://127.0.0.1:1234/v1`.
- Compatible hosted endpoints include OpenAI, OpenRouter, DeepSeek, Groq, Together, and custom OpenAI-compatible servers, subject to their API compatibility.
- For Ollama and LM Studio, install/pull a model locally and start the local server first. No cloud API key is required.
- Use Settings → provider selection, endpoint, API key, connection test, and model discovery. Model IDs can also be typed manually.
- Provider credentials and endpoint settings are stored in the current Windows user's `%APPDATA%/SHZ PaperOrchestra/.env`; do not commit this file or share it.

## Literature discovery

Candidate discovery is decoupled from Google Search and queries OpenAlex and Crossref. Candidate records are subsequently enriched through the existing Semantic Scholar integration. Internet access is still required for scholarly discovery and metadata enrichment.

## Run and build

- Windows x64; Python 3.11 for development.
- Install: `pip install -r requirements.txt -r desktop/requirements.txt`.
- Run: `python desktop_app.py` from the repository root.
- Projects are saved in `Documents/SHZ PaperOrchestra/Projects`.
- The Windows workflow builds an Inno Setup installer.
- A local TeX distribution may be required to compile the final PDF.
- The upstream dataset is not included; the app does not invent it.

## Important compatibility note

The provider adapter routes the shared text, image, and PDF LLM calls through OpenAI-compatible APIs. Some optional upstream features remain vendor-specific; test the selected provider with the actual project workload before relying on a production paper run.
