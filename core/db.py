# -*- coding: utf-8 -*-
"""
Lapisan penyimpanan SQLite (stdlib sqlite3) — tanpa dependensi tambahan.
Skema:
  articles(id, fingerprint UNIQUE, source_id, source_name, country, lang,
           title, summary, link, published, fetched_at,
           sentiment, label, category, category_name, horizons_json,
           sectors_json, analysis_json)
  signals(date, sector, name, direction_short, direction_medium, direction_long,
           net_short, net_medium, net_long, article_count, top_headlines_json,
           tickers_json, summary)  UNIQUE(date, sector)
  meta(key, value)
"""
import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import config


def _now():
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init()

    def _init(self):
        with _connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT UNIQUE,
                    source_id TEXT,
                    source_name TEXT,
                    country TEXT,
                    lang TEXT,
                    title TEXT,
                    summary TEXT,
                    link TEXT,
                    published TEXT,
                    fetched_at TEXT,
                    sentiment REAL,
                    label TEXT,
                    category TEXT,
                    category_name TEXT,
                    horizons_json TEXT,
                    sectors_json TEXT,
                    analysis_json TEXT
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    sector TEXT,
                    name TEXT,
                    direction_short TEXT,
                    direction_medium TEXT,
                    direction_long TEXT,
                    net_short REAL,
                    net_medium REAL,
                    net_long REAL,
                    article_count INTEGER,
                    top_headlines_json TEXT,
                    tickers_json TEXT,
                    summary TEXT,
                    UNIQUE(date, sector)
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    horizon TEXT,
                    code TEXT,
                    name TEXT,
                    sector TEXT,
                    sector_name TEXT,
                    score REAL,
                    article_count INTEGER,
                    UNIQUE(date, horizon, code)
                )""")
            # migrasi ringan: tambahkan kolom sector_name bila belum ada
            try:
                conn.execute("ALTER TABLE recommendations ADD COLUMN sector_name TEXT")
            except sqlite3.OperationalError:
                pass
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    ticker TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY(ticker, date)
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rec_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    horizon TEXT,
                    code TEXT,
                    name TEXT,
                    sector TEXT,
                    sector_name TEXT,
                    entry_price REAL,
                    current_price REAL,
                    pct_change REAL,
                    signal_dir TEXT,
                    outcome TEXT,
                    checked_at TEXT,
                    UNIQUE(date, horizon, code)
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_feedback (
                    horizon TEXT,
                    sector TEXT,
                    correct INTEGER DEFAULT 0,
                    total INTEGER DEFAULT 0,
                    PRIMARY KEY(horizon, sector)
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )""")
            conn.commit()

    # ---------- ARTICLES ----------
    def insert_article(self, a, analysis):
        with _connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO articles
                (fingerprint, source_id, source_name, country, lang,
                 title, summary, link, published, fetched_at,
                 sentiment, label, category, category_name,
                 horizons_json, sectors_json, analysis_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(fingerprint) DO UPDATE SET
                    source_id = excluded.source_id,
                    source_name = excluded.source_name,
                    title = excluded.title,
                    summary = excluded.summary,
                    link = excluded.link,
                    published = excluded.published,
                    fetched_at = excluded.fetched_at,
                    sentiment = excluded.sentiment,
                    label = excluded.label,
                    category = excluded.category,
                    category_name = excluded.category_name,
                    horizons_json = excluded.horizons_json,
                    sectors_json = excluded.sectors_json,
                    analysis_json = excluded.analysis_json
            """, (
                a["fingerprint"], a.get("source_id"), a.get("source_name"),
                a.get("country"), a.get("lang"),
                a.get("title"), a.get("summary"), a.get("link"),
                a.get("published").isoformat() if a.get("published") else None,
                _now(),
                analysis.get("sentiment"), analysis.get("label"),
                analysis.get("category"), analysis.get("category_name"),
                json.dumps(analysis.get("horizons", [])),
                json.dumps(analysis.get("sectors", {})),
                json.dumps(analysis, ensure_ascii=False),
            ))
            conn.commit()
            return True

    def recent_articles(self, limit=60, after_date=None):
        # Ambil lebih banyak lalu saring di Python agar tidak bergantung pada
        # parsing tanggal SQLite (format ISO + offset zona waktu).
        with _connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT * FROM articles ORDER BY published DESC LIMIT ?
            """, (max(limit * 10, 2000),)).fetchall()
        items = [dict(r) for r in rows]
        if after_date:
            items = [x for x in items if (x.get("published") or "")[:10] >= after_date]
        return items[:limit]

    def article_count(self):
        with _connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"]

    def counts_by_label(self):
        with _connect(self.db_path) as conn:
            return {r["label"]: r["c"] for r in
                    conn.execute("SELECT label, COUNT(*) c FROM articles GROUP BY label").fetchall()}

    # ---------- SIGNALS ----------
    def save_signals(self, day, signals):
        with _connect(self.db_path) as conn:
            for sig in signals:
                conn.execute("""
                    INSERT OR REPLACE INTO signals
                    (date, sector, name, direction_short, direction_medium, direction_long,
                     net_short, net_medium, net_long, article_count,
                     top_headlines_json, tickers_json, summary)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    day, sig["sector"], sig["name"],
                    sig.get("direction_short"), sig.get("direction_medium"),
                    sig.get("direction_long"),
                    sig.get("net_short", 0), sig.get("net_medium", 0),
                    sig.get("net_long", 0), sig.get("article_count", 0),
                    json.dumps(sig.get("top_headlines", []), ensure_ascii=False),
                    json.dumps(sig.get("tickers", []), ensure_ascii=False),
                    sig.get("summary", ""),
                ))
            conn.commit()

    def signals_for_date(self, day):
        with _connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT * FROM signals WHERE date = ? ORDER BY article_count DESC
            """, (day,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["top_headlines"] = json.loads(d.pop("top_headlines_json") or "[]")
            d["tickers"] = json.loads(d.pop("tickers_json") or "[]")
            out.append(d)
        return out

    def latest_signal_date(self):
        with _connect(self.db_path) as conn:
            r = conn.execute("SELECT MAX(date) d FROM signals").fetchone()
            return r["d"] if r and r["d"] else None

    # ---------- RECOMMENDATIONS ----------
    def save_recommendations(self, day, recs):
        with _connect(self.db_path) as conn:
            conn.execute("DELETE FROM recommendations WHERE date = ?", (day,))
            for r in recs:
                conn.execute("""
                    INSERT OR REPLACE INTO recommendations
                    (date, horizon, code, name, sector, sector_name, score, article_count)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (day, r["horizon"], r["code"], r["name"],
                      r["sector"], r.get("sector_name", ""),
                      r["score"], r["article_count"]))
            conn.commit()

    def recommendations_for_date(self, day):
        with _connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT * FROM recommendations WHERE date = ?
                ORDER BY horizon, score DESC
            """, (day,)).fetchall()
        out = defaultdict(list)
        for r in rows:
            out[r["horizon"]].append(dict(r))
        return out

    # ---------- PRICES ----------
    def upsert_prices(self, ticker, rows):
        with _connect(self.db_path) as conn:
            for r in rows:
                conn.execute("""
                    INSERT OR REPLACE INTO prices
                    (ticker, date, open, high, low, close, volume)
                    VALUES (?,?,?,?,?,?,?)
                """, (ticker, r["date"], r.get("open"), r.get("high"),
                      r.get("low"), r.get("close"), r.get("volume")))
            conn.commit()

    def get_prices(self, ticker, limit=None):
        with _connect(self.db_path) as conn:
            sql = "SELECT * FROM prices WHERE ticker=? ORDER BY date ASC"
            params = [ticker]
            if limit:
                sql += " LIMIT ?"
                params.append(int(limit))
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def price_latest(self, ticker):
        with _connect(self.db_path) as conn:
            r = conn.execute(
                "SELECT close, date FROM prices WHERE ticker=? ORDER BY date DESC LIMIT 1",
                (ticker,)).fetchone()
        return dict(r) if r else None

    # ---------- PERFORMANCE & MODEL FEEDBACK ----------
    def all_recommendations(self, limit=500):
        with _connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM recommendations ORDER BY date DESC, score DESC LIMIT ?",
                (limit,)).fetchall()
        return [dict(r) for r in rows]

    def performance_exists(self, date, horizon, code):
        with _connect(self.db_path) as conn:
            r = conn.execute(
                "SELECT 1 FROM rec_performance WHERE date=? AND horizon=? AND code=? LIMIT 1",
                (date, horizon, code)).fetchone()
        return r is not None

    def save_performance(self, rec):
        with _connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO rec_performance
                (date, horizon, code, name, sector, sector_name,
                 entry_price, current_price, pct_change, signal_dir, outcome, checked_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (rec["date"], rec["horizon"], rec["code"], rec.get("name", ""),
                  rec.get("sector", ""), rec.get("sector_name", ""),
                  rec.get("entry_price"), rec.get("current_price"),
                  rec.get("pct_change"), rec.get("signal_dir", "bullish"),
                  rec.get("outcome"), _now()))
            conn.commit()

    def performance_rows(self, limit=200):
        with _connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM rec_performance ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
        return [dict(r) for r in rows]

    def bump_feedback(self, horizon, sector, correct):
        with _connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO model_feedback (horizon, sector, correct, total)
                VALUES (?,?,?,1)
                ON CONFLICT(horizon, sector) DO UPDATE SET
                    correct = model_feedback.correct + excluded.correct,
                    total = model_feedback.total + 1
            """, (horizon, sector, 1 if correct else 0))
            conn.commit()

    def model_feedback_all(self):
        with _connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM model_feedback").fetchall()
        return [dict(r) for r in rows]

    # ---------- META ----------
    def set_meta(self, key, value):
        with _connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?,?)",
                         (key, str(value)))
            conn.commit()

    def get_meta(self, key, default=None):
        with _connect(self.db_path) as conn:
            r = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return r["value"] if r else default
