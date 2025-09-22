import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "aiagent.db")


def get_connection() -> sqlite3.Connection:
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def init_db() -> None:
	conn = get_connection()
	try:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS reports (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				query TEXT NOT NULL,
				created_at TEXT NOT NULL,
				summary TEXT NOT NULL,
				sources_json TEXT NOT NULL
			);
			"""
		)
		conn.commit()
	finally:
		conn.close()


def save_report(query: str, summary: str, sources: List[Dict[str, Any]]) -> int:
	conn = get_connection()
	try:
		created_at = datetime.utcnow().isoformat()
		sources_json = json.dumps(sources, ensure_ascii=False)
		cur = conn.execute(
			"INSERT INTO reports (query, created_at, summary, sources_json) VALUES (?, ?, ?, ?)",
			(query, created_at, summary, sources_json),
		)
		conn.commit()
		return int(cur.lastrowid)
	finally:
		conn.close()


def list_reports(limit: int = 50) -> List[Dict[str, Any]]:
	conn = get_connection()
	try:
		rows = conn.execute(
			"SELECT id, query, created_at FROM reports ORDER BY id DESC LIMIT ?",
			(limit,),
		).fetchall()
		return [dict(row) for row in rows]
	finally:
		conn.close()


def get_report(report_id: int) -> Optional[Dict[str, Any]]:
	conn = get_connection()
	try:
		row = conn.execute(
			"SELECT id, query, created_at, summary, sources_json FROM reports WHERE id = ?",
			(report_id,),
		).fetchone()
		if not row:
			return None
		data = dict(row)
		data["sources"] = json.loads(data.get("sources_json", "[]"))
		return data
	finally:
		conn.close()
