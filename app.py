import os
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash

from db import init_db, save_report, list_reports, get_report
from agent import run_agent

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

init_db()


@app.get("/")
def index():
	reports = list_reports(limit=100)
	missing_keys = []
	if not os.getenv("TAVILY_API_KEY"):
		missing_keys.append("TAVILY_API_KEY")
	if not os.getenv("OPENAI_API_KEY"):
		missing_keys.append("OPENAI_API_KEY")
	return render_template("index.html", reports=reports, missing_keys=missing_keys)


@app.post("/run")
def run():
	query = (request.form.get("query") or "").strip()
	if not query:
		flash("Please enter a query.", "error")
		return redirect(url_for("index"))
	try:
		result: Dict[str, Any] = run_agent(query)
		report_id = save_report(query, result["summary"], result["sources"])
		if result.get("errors"):
			flash(f"Some sources were skipped: {len(result['errors'])}", "warning")
		return redirect(url_for("view_report", report_id=report_id))
	except Exception as e:
		flash(str(e), "error")
		return redirect(url_for("index"))


@app.get("/report/<int:report_id>")
def view_report(report_id: int):
	report = get_report(report_id)
	if not report:
		flash("Report not found.", "error")
		return redirect(url_for("index"))
	return render_template("report.html", report=report)


if __name__ == "__main__":
	port = int(os.getenv("PORT", "5000"))
	app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
