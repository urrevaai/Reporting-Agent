## AI Research Agent

A minimal Flask-based agent that:
- Searches the web (Tavily API)
- Extracts content (trafilatura for HTML, pypdf for PDFs)
- Summarizes with Gemini
- Saves reports to SQLite
- Provides a simple web UI for history and viewing reports

### Setup
1. Create and fill `.env`:
```
TAVILY_API_KEY=your_tavily_key
GEMINI_API_KEY=your_gemini_key
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
```

2. Install dependencies (Python 3.10+ recommended):
```
pip install -r requirements.txt
```

3. Run the app:
```
python app.py
```

Visit http://localhost:5000.

### Notes
- If a page blocks scraping or fails extraction, it will be skipped with a note.
- Only the top 2–3 sources are used for the report.
- Data is stored in `aiagent.db` (SQLite) in the project root.

### Environment
- **Web Search**: Tavily API
- **Extractors**: trafilatura (HTML) + pypdf (PDF)
- **LLM**: Gemini (`gemini-1.5-flash` by default)

### Troubleshooting
- **Missing API keys**: The app will show a friendly error. Set keys in `.env`.
- **SSL errors on Windows**: ensure `certifi` is up to date (`pip install -U certifi`).
- **PDFs**: Some are scans; pypdf cannot OCR.
