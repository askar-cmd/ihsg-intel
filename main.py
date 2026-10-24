# -*- coding: utf-8 -*-
"""
Aplikasi FastAPI — Pasar Intel IHSG.
Menjalankan dashboard web + API + scheduler harian.

Jalankan:
    pip install -r requirements.txt
    python main.py            # lalu buka http://localhost:8000
"""
import json
import os
import sys
from contextlib import asynccontextmanager

# Perbaikan stabilitas Windows: asyncio ProactorEventLoop (default) punya bug
# yang membuat loop accept gagal (WinError 64) setelah berjalan lama. Pakai
# SelectorEventLoop yang lebih stabil untuk beban server ini.
if sys.platform == "win32":
    import asyncio
    try:
        _policy = asyncio.WindowsSelectorEventLoopPolicy()
        asyncio.set_event_loop_policy(_policy)
        # pastikan loop baru yang dibuat uvicorn memakai policy selector ini
        asyncio.set_event_loop(_policy.new_event_loop())
    except Exception:
        pass

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
from core import db as dbmod
from core.analyzer import run_pipeline, today_str
from core.seed import seed_if_empty
from core.learn import (evaluate_recommendations, model_summary,
                        get_model_weights, sync_prices_for_tickers,
                        filter_active_recommendations)
from core.themes import (evaluate_themes, build_long_recommendations,
                         theme_sectors_stocks, theme_articles)
from core.drivers import evaluate_drivers
from core.prices import fetch_price_history
from scheduler import start_scheduler, shutdown

db = dbmod.Database()


def _fmt_sgt(iso):
    """Menormalisasi timestamp ISO ke zona waktu SGT (+8) dan format dd-mm-yyyy HH:MM."""
    if not iso:
        return None
    try:
        from datetime import datetime
        # ubah menjadi aware datetime
        s = str(iso).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=__import__("datetime").timezone.utc)
        try:
            from zoneinfo import ZoneInfo
            sgt = ZoneInfo("Asia/Singapore")
        except Exception:
            from datetime import timezone, timedelta
            sgt = timezone(timedelta(hours=8))
        local = dt.astimezone(sgt)
        return local.strftime("%d-%m-%Y %H:%M")
    except Exception:
        return str(iso)


@asynccontextmanager
async def lifespan(app):
    # isi data contoh jika DB kosong (agar dashboard langsung tampil)
    try:
        seed_if_empty(db)
    except Exception as e:
        print("[startup] seed warning:", e)
    # jalankan satu siklus di latar belakang + jadwal harian
    start_scheduler()
    yield
    shutdown()


app = FastAPI(title=config.APP_NAME, description=config.APP_DESC,
              version="1.0.0", lifespan=lifespan)

# mount static dashboard
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "articles": db.article_count(),
        "last_run": db.get_meta("last_run"),
        "last_run_day": db.get_meta("last_run_day"),
    }


def _article_has_ticker(a, code):
    """Benar jika artikel menyebut ticker tertentu (dari hasil analisis)."""
    try:
        analysis = json.loads(a.get("analysis_json") or "{}")
    except Exception:
        return False
    code = code.upper()
    for sec in analysis.get("sectors", {}).values():
        for t in sec.get("tickers", []):
            if t.get("code", "").upper() == code:
                return True
    return False


def _ticker_sector(code):
    """Mengembalikan kode sektor tempat sebuah saham berada, atau None."""
    info = config.STOCKS.get(code.upper())
    return info.get("sector") if info else None


def _article_has_sector(a, sec_key):
    """Benar jika artikel termasuk dalam sektor tertentu."""
    try:
        analysis = json.loads(a.get("analysis_json") or "{}")
    except Exception:
        return False
    return sec_key in analysis.get("sectors", {})


@app.get("/api/news")
async def news(limit: int = Query(50, ge=1, le=500), date: str = Query(None),
               ticker: str = Query(None), sector: str = Query(None),
               driver: str = Query(None)):
    # Saat difilter, ambil cakupan lebih luas dulu (agar hasil filter lengkap),
    # lalu potong sesuai `limit`. Default ke hari sinyal terbaru agar cocok
    # dengan angka pada matriks (jumlah berita per hari).
    if (ticker or sector) and not date:
        date = db.latest_signal_date() or today_str()
    if ticker or sector:
        arts = db.recent_articles(limit=1000, after_date=date)
    else:
        arts = db.recent_articles(limit=limit, after_date=date)
    if ticker:
        # tampilkan artikel yang menyebut ticker ATAU artikel dari sektor saham
        # tersebut (fallback rekomendasi berbasis sektor). Ini memastikan
        # setiap saham rekomendasi selalu punya daftar berita pendukung.
        sec_key = _ticker_sector(ticker)
        arts = [a for a in arts
                if _article_has_ticker(a, ticker)
                or (sec_key and _article_has_sector(a, sec_key))]
    if sector:
        arts = [a for a in arts if _article_has_sector(a, sector)]
    if driver:
        drv = next((d for d in config.MARKET_DRIVERS if d["id"] == driver), None)
        if drv:
            kws = [k.lower() for k in drv["keywords"]]
            arts = [a for a in arts
                    if any(k in (a.get("title", "") + " " + a.get("summary", "")).lower()
                           for k in kws)]
    return {"articles": arts[:limit]}


@app.get("/api/signals")
async def signals(date: str = Query(None)):
    day = date or db.latest_signal_date() or today_str()
    return {"date": day, "signals": db.signals_for_date(day)}


def _merge_long_recs(db, news_recs, min_score=0.4):
    """Gabungkan rekomendasi panjang dari berita + tema struktural,
    dengan keberagaman tema agar setiap tren (El Niño, pangan, BBM, dll.)
    terwakili di panel jangka panjang."""
    struct_recs, _ = build_long_recommendations(db, min_score=min_score)
    combined = {r["code"]: r for r in (news_recs.get("long") or [])}
    for r in struct_recs:
        cur = combined.get(r["code"])
        if cur is None or r["score"] > cur.get("score", 0):
            combined[r["code"]] = r

    top = config.TOP_RECOMMENDATIONS
    # 1) pilih yang terbaik per tema (paling banyak satu per tema)
    by_theme = {}
    order = []
    for r in sorted(combined.values(), key=lambda x: -x["score"]):
        theme = r.get("theme") or r.get("source") or ""
        if theme not in by_theme:
            by_theme[theme] = r
            order.append(r)
        if len(order) >= top:
            break
    # 2) isi sisa slot dengan top global yang belum terpilih
    if len(order) < top:
        for r in sorted(combined.values(), key=lambda x: -x["score"]):
            if all(r["code"] != o["code"] for o in order):
                order.append(r)
            if len(order) >= top:
                break
    out = dict(news_recs)
    out["long"] = order
    return out


@app.get("/api/recommendations")
async def recommendations(date: str = Query(None)):
    day = date or db.latest_signal_date() or today_str()
    recs = db.recommendations_for_date(day)
    recs = _merge_long_recs(db, recs)
    active, suspended = filter_active_recommendations(db, recs)
    return {"date": day, "recommendations": active, "suspended": suspended}


@app.get("/api/themes")
async def themes():
    return {"themes": evaluate_themes(db)}


@app.get("/api/drivers")
async def drivers():
    return {"drivers": evaluate_drivers(db)}


@app.get("/api/themes/{theme_id}")
async def theme_detail(theme_id: str):
    theme = next((t for t in config.STRUCTURAL_THEMES if t["id"] == theme_id), None)
    if not theme:
        return {"error": "tema tidak ditemukan"}
    sectors = theme_sectors_stocks(theme)
    articles = theme_articles(db, theme_id)
    summary = {
        "id": theme["id"],
        "name": theme["name"],
        "description": theme.get("description", ""),
        "articles": len(articles),
        "sectors": sectors,
        "news": [
            {
                "title": a.get("title"),
                "summary": a.get("summary"),
                "link": a.get("link"),
                "source_name": a.get("source_name"),
                "published": a.get("published"),
                "analysis": a.get("analysis_json"),
            }
            for a in articles
        ],
    }
    return summary


@app.get("/api/sectors")
async def sectors():
    return {
        "sectors": [
            {"code": k, "name": v["name"], "keyword_count": len(v["keywords"]),
             "ticker_count": len(v["tickers"]), "tickers": v["tickers"]}
            for k, v in config.SECTORS.items()
        ]
    }


@app.get("/api/dashboard")
async def dashboard():
    day = db.latest_signal_date() or today_str()
    sigs = db.signals_for_date(day)
    arts = db.recent_articles(limit=20)
    recs = db.recommendations_for_date(day)
    recs = _merge_long_recs(db, recs)
    active, suspended = filter_active_recommendations(db, recs)
    themes_out = evaluate_themes(db)
    drivers_out = evaluate_drivers(db)
    return {
        "date": day,
        "signals": sigs,
        "recommendations": active,
        "suspended": suspended,
        "themes": themes_out,
        "drivers": drivers_out,
        "recent_news": arts,
        "totals": {
            "articles": db.article_count(),
            "by_label": db.counts_by_label(),
            "sectors_count": len(config.SECTORS),
            "sources_count": len(config.SOURCES),
        },
        "horizons": {k: v["label"] for k, v in config.HORIZONS.items()},
        "last_prediction_update": _fmt_sgt(db.get_meta("last_prediction_update")),
    }


@app.post("/api/refresh")
async def refresh():
    res = run_pipeline(fetch=True)
    return res


@app.get("/api/model")
async def model():
    return {
        "model": model_summary(db),
        "weights": {f"{h}|{s}": w for (h, s), w in get_model_weights(db).items()},
        "performances": db.performance_rows(limit=30),
        "last_prediction_update": _fmt_sgt(db.get_meta("last_prediction_update")),
    }


@app.post("/api/check")
async def check():
    """Perbarui prediksi: sinkronkan harga + evaluasi rekomendasi masa lalu."""
    res = evaluate_recommendations(db)
    return res


@app.get("/api/price")
async def price(code: str = Query(...)):
    code = code.strip().upper()
    series = db.get_prices(code)
    if not series:
        rows = fetch_price_history(code)
        if rows:
            db.upsert_prices(code, rows)
            series = db.get_prices(code)
    return {"code": code, "prices": series[-int(config.PRICE_HISTORY_DAYS):]}


@app.get("/api/prices")
async def prices():
    """Data harga + performa untuk saham-saham yang masuk rekomendasi hari ini."""
    day = db.latest_signal_date() or today_str()
    recs, _ = filter_active_recommendations(db, db.recommendations_for_date(day))
    seen = set()
    ordered = []
    for h in ("short", "medium", "long"):
        for r in recs.get(h, [])[: config.PRICE_WATCH_LIMIT]:
            if r["code"] in seen:
                continue
            seen.add(r["code"])
            ordered.append(r)

    out = []
    for r in ordered:
        series = db.get_prices(r["code"])
        if not series:
            rows = fetch_price_history(r["code"])
            if rows:
                db.upsert_prices(r["code"], rows)
                series = db.get_prices(r["code"])
        latest = db.price_latest(r["code"])
        out.append({
            "code": r["code"],
            "name": r.get("name", ""),
            "sector_name": r.get("sector_name", r.get("sector", "")),
            "horizon": r["horizon"],
            "series": series[-120:],
            "latest_close": latest["close"] if latest else None,
            "latest_date": latest["date"] if latest else None,
        })
    m = model_summary(db)
    m["last_prediction_update"] = _fmt_sgt(db.get_meta("last_prediction_update"))
    return {"watch": out, "model": m, "date": day}


@app.get("/api/config")
async def api_config():
    return {
        "horizons": config.HORIZONS,
        "categories": {k: v["name"] for k, v in config.CATEGORIES.items()},
        "sources": config.SOURCES,
        "recommendation_min_score": config.RECOMMENDATION_MIN_SCORE,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
