## AI Research Agent

A minimal Flask-based agent that:
- Searches the web (Tavily API)
- Extracts content (trafilatura for HTML, pypdf for PDFs)
- Summarizes with Gemini
- Saves reports to SQLite
- Provides a simple web UI for history and viewing reports

How it works (Architecture)
Plain-language flow:
1) You submit a query in the web UI.
2) Agent calls Tavily Search to find 2–3 sources (articles, PDFs).
3) Agent downloads each URL and extracts clean text:
   - HTML → trafilatura
   - PDF → pypdf
   If extraction fails or is blocked, the source is skipped gracefully.
4) Agent sends the aggregated content to Gemini to produce a concise report.
5) Report (query, summary, sources, timestamp) is saved to SQLite.
6) The homepage shows a history list; you can click any report to view it.

### Setup
1. Create and fill `.env`:
```
TAVILY_API_KEY=your_tavily_key
GEMINI_API_KEY=your_gemini_key
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

## Where AI help was used
- Code scaffolding and glue logic for the Flask app and agent pipeline
- Error handling patterns and README wording

### Environment
- **Web Search**: Tavily API
- **Extractors**: trafilatura (HTML) + pypdf (PDF)
- **LLM**: Gemini (`gemini-1.5-flash` by default)
