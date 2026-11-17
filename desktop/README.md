# SHZ PaperOrchestra for Windows

This desktop shell invokes the original PaperOrchestra CLI and agents; it does not simulate the research pipeline.

- Windows x64, Python 3.11 for development.
- Install: `pip install -r requirements.txt -r desktop/requirements.txt`.
- Run: `python desktop_app.py` from the repository root.
- Projects are saved in Documents/SHZ PaperOrchestra/Projects.
- API keys are stored locally under %APPDATA%/SHZ PaperOrchestra/.env.
- The Windows workflow builds an Inno Setup installer.
- Internet, provider credentials and potentially a local TeX distribution are required.
- The upstream dataset is not included; the app does not invent it.
