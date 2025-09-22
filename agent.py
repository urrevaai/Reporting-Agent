import os
import re
from typing import Any, Dict, List, Optional

import requests
from pypdf import PdfReader
import trafilatura
from trafilatura.settings import use_config
import google.generativeai as genai


def tavily_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
	api_key = os.getenv("TAVILY_API_KEY")
	if not api_key:
		raise RuntimeError("Missing TAVILY_API_KEY. Set it in environment or .env")
	resp = requests.post(
		"https://api.tavily.com/search",
		json={
			"api_key": api_key,
			"query": query,
			"include_answer": False,
			"max_results": max_results,
		},
		timeout=20,
	)
	if resp.status_code != 200:
		raise RuntimeError(f"Search failed with status {resp.status_code}: {resp.text[:200]}")
	payload = resp.json()
	results = payload.get("results", [])
	out: List[Dict[str, Any]] = []
	for r in results:
		out.append(
			{
				"title": r.get("title") or "Untitled",
				"url": r.get("url"),
				"snippet": r.get("content") or r.get("snippet") or "",
			}
		)
	return out[:max_results]


def is_pdf_url(url: str, headers: Optional[Dict[str, str]]) -> bool:
	if headers and headers.get("Content-Type", "").lower().startswith("application/pdf"):
		return True
	return bool(re.search(r"\.pdf(\?|$)", url, re.IGNORECASE))


def fetch_url(url: str) -> Dict[str, Any]:
	try:
		resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 AI-Agent/1.0"}, timeout=25)
		return {"ok": True, "response": resp}
	except Exception as e:
		return {"ok": False, "error": str(e)}


def extract_text_from_pdf_bytes(data: bytes) -> str:
	try:
		from io import BytesIO
		reader = PdfReader(BytesIO(data))
		texts = []
		for page in reader.pages:
			try:
				texts.append(page.extract_text() or "")
			except Exception:
				continue
		return "\n".join([t for t in texts if t]).strip()
	except Exception:
		return ""


def extract_text_from_html(url: str, html: str) -> str:
	cfg = use_config()
	cfg.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
	cfg.set("DEFAULT", "MIN_EXTRACTED_SIZE", "200")
	try:
		return trafilatura.extract(html, url=url, config=cfg) or ""
	except Exception:
		return ""


def extract_content(url: str) -> Dict[str, Any]:
	fetch = fetch_url(url)
	if not fetch.get("ok"):
		return {"url": url, "ok": False, "reason": f"Fetch error: {fetch.get('error')}"}
	resp = fetch["response"]
	content_type = resp.headers.get("Content-Type", "").lower()
	data = resp.content
	if is_pdf_url(url, resp.headers) or content_type.startswith("application/pdf"):
		text = extract_text_from_pdf_bytes(data)
		if not text:
			return {"url": url, "ok": False, "reason": "Unable to extract text from PDF"}
		return {"url": url, "ok": True, "text": text, "type": "pdf"}
	else:
		html = resp.text
		text = extract_text_from_html(url, html)
		if not text:
			return {"url": url, "ok": False, "reason": "Unable to extract text from HTML"}
		return {"url": url, "ok": True, "text": text, "type": "html"}


def build_summarization_prompt(query: str, sources: List[Dict[str, Any]]) -> str:
	parts = [
		"You are a precise research assistant. Summarize findings in 6-10 bullet points.",
		"Focus on concrete facts, consensus, and cite sources by [n].",
		"Add a short 'Key Takeaways' section and include links at end.",
		f"User query: {query}",
		"\nSources:",
	]
	for i, s in enumerate(sources, start=1):
		content_preview = (s.get("text", "")[:1500]).replace("\n", " ")
		parts.append(f"[{i}] {s.get('title') or 'Source'} - {s.get('url')} :: {content_preview}")
	return "\n".join(parts)


def summarize_with_gemini(query: str, sources: List[Dict[str, Any]]) -> str:
	api_key = os.getenv("GEMINI_API_KEY")
	if not api_key:
		raise RuntimeError("Missing GEMINI_API_KEY. Set it in environment or .env")
	genai.configure(api_key=api_key)
	model = genai.GenerativeModel("gemini-1.5-flash")
	prompt = build_summarization_prompt(query, sources)
	resp = model.generate_content(prompt)
	return (resp.text or "").strip()


def run_agent(query: str) -> Dict[str, Any]:
	search_results = tavily_search(query, max_results=3)
	if not search_results:
		raise RuntimeError("No search results found.")

	extracted: List[Dict[str, Any]] = []
	errors: List[Dict[str, str]] = []
	for r in search_results[:3]:
		url = r.get("url")
		if not url:
			continue
		res = extract_content(url)
		if res.get("ok"):
			res["title"] = r.get("title")
			extracted.append(res)
		else:
			errors.append({"url": url, "reason": res.get("reason", "Unknown error")})

	usable_sources = [
		{"title": s.get("title"), "url": s.get("url"), "text": s.get("text")}
		for s in extracted
	]
	if len(usable_sources) == 0:
		raise RuntimeError("All candidate sources failed to extract. Try a different query.")

	summary = summarize_with_gemini(query, usable_sources)
	links = [{"title": s.get("title"), "url": s.get("url")} for s in usable_sources]
	return {"summary": summary, "sources": links, "errors": errors}
