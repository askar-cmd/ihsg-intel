# -*- coding: utf-8 -*-
"""
Orkestrator analisis: berita -> klasifikasi -> sinyal sektor harian.

Alur satu siklus (dijalankan otomatis oleh scheduler):
  1. Ambil berita dari RSS.
  2. Klasifikasi tiap artikel (sentimen, sektor, kategori, horizon).
  3. Simpan artikel ke SQLite.
  4. Agregasi sinyal per sektor per horizon (pendek/menengah/panjang).
  5. Simpan sinyal harian.
"""
import json
from collections import defaultdict
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
    SGT = ZoneInfo("Asia/Singapore")
except Exception:
    SGT = None

import config
from core import db as dbmod
from core.classify import classify_article
from core.fetch_news import fetch_all
from core.learn import get_model_weights
from core.drivers import build_driver_votes


def now_wib():
    if SGT:
        return datetime.now(SGT)
    return datetime.now()


def today_str():
    return now_wib().strftime("%Y-%m-%d")


def _direction(net, count):
    """net sudah dibagi normalisasi; threshold kecil."""
    if count == 0:
        return "netral"
    if net >= config.SENTIMENT_THRESHOLD:
        return "bullish"
    if net <= -config.SENTIMENT_THRESHOLD:
        return "bearish"
    return "netral"


def aggregate_day(db, day=None, articles=None):
    """
    Menghitung sinyal sektor untuk satu hari dari artikel yang disimpan.
    Jika `articles` diberikan, gunakan itu; jika tidak, ambil artikel dari DB
    yang tanggal published-nya == day.
    """
    day = day or today_str()
    if articles is None:
        articles = db.recent_articles(after_date=day, limit=2000)
        # tampung yang exact di hari itu
        articles = [a for a in articles if (a.get("published") or "")[:10] == day]

    # struktur agregasi: sector -> {horizon: net, count, headlines[], tickers{}}
    # bobot "belajar" dari akurasi riwayat (per sektor/horizon)
    learn_weights = get_model_weights(db)

    agg = {}
    for a in articles:
        analysis = json.loads(a.get("analysis_json") or "{}")
        if not analysis:
            continue
        sectors = analysis.get("sectors", {})
        horizons = analysis.get("horizons", ["medium"])
        sent = analysis.get("sentiment", 0.0)
        label = analysis.get("label", "netral")
        title = a.get("title", "")
        for sec_key, info in sectors.items():
            s = agg.setdefault(sec_key, {
                "name": info["name"],
                "net": {h: 0.0 for h in config.HORIZONS},
                "count": 0,
                "bull": [],
                "bear": [],
                "tickers": {},
                "votes": {h: {} for h in config.HORIZONS},
            })
            s["count"] += 1
            w = info.get("weight", 1.0)
            for h in horizons:
                if h not in s["net"]:
                    continue
                eff = w * learn_weights.get((h, sec_key), 1.0)
                s["net"][h] += sent * eff
            # langsiran headline & ticker
            sec_tickers = info.get("tickers", [])
            for t in sec_tickers:
                s["tickers"].setdefault(t["code"], t)
            # kumpulkan "suara" ticker per horizon untuk rekomendasi.
            # Hanya berita dengan sentimen positif disertakan (bullish).
            if sent > 0:
                for h in horizons:
                    if h not in s["votes"]:
                        continue
                    eff = w * learn_weights.get((h, sec_key), 1.0)
                    for t in sec_tickers:
                        vote = s["votes"][h].get(t["code"])
                        if vote is None:
                            vote = {"score": 0.0, "count": 0,
                                    "code": t["code"],
                                    "name": t["name"], "sector": sec_key,
                                    "sector_name": info["name"]}
                            s["votes"][h][t["code"]] = vote
                        vote["score"] += sent * eff
                        vote["count"] += 1
            if label == "bullish":
                s["bull"].append(title)
            elif label == "bearish":
                s["bear"].append(title)

    signals = []
    for sec_key, s in agg.items():
        net_s = s["net"]["short"]
        net_m = s["net"]["medium"]
        net_l = s["net"]["long"]
        # normalisasi oleh jumlah artikel agar sebanding
        n = max(1, s["count"])
        signals.append({
            "sector": sec_key,
            "name": s["name"],
            "direction_short": _direction(net_s / n, s["count"]),
            "direction_medium": _direction(net_m / n, s["count"]),
            "direction_long": _direction(net_l / n, s["count"]),
            "net_short": round(net_s / n, 4),
            "net_medium": round(net_m / n, 4),
            "net_long": round(net_l / n, 4),
            "article_count": s["count"],
            "top_headlines": s["bull"][:5] + s["bear"][:5],
            "tickers": list(s["tickers"].values()),
            "summary": _build_summary(s),
        })
    db.save_signals(day, signals)

    # Tambahkan vote dari pendorong pasar (suku bunga, emas, komoditas,
    # perang, bitcoin) untuk horizon pendek & menengah.
    driver_votes, driver_summary = build_driver_votes(db)

    # Bangun rekomendasi saham per horizon.
    # - "vote" eksplisit: saham yang benar2 disebut di berita
    # - fallback sektor: bila sektor punya net sentimen positif, saham2nya
    #   masuk kandidat (dengan skor diperkecil) agar rekomendasi tetap terisi.
    recs = []
    for h in config.HORIZONS:
        pool = {}
        # 1) suara eksplisit
        for sec in agg.values():
            for code, v in sec["votes"].get(h, {}).items():
                cur = pool.get(code)
                if cur is None or v["score"] > cur["score"]:
                    pool[code] = v
        # 2) fallback sektor: jangkau seluruh ticker sektor (dari config)
        #     yang memiliki net sentimen positif untuk horizon ini.
        for sec_key, sec in agg.items():
            n = max(1, sec["count"])
            net = sec["net"].get(h, 0.0) / n
            if net <= 0.02:
                continue
            full_sec = config.SECTORS.get(sec_key)
            if not full_sec:
                continue
            # skor fallback: sebanding dgn kekuatan net sektor, diperbesar agar
            # bisa melewati ambang rekomendasi (maks ~2.0).
            fallback_score = min(2.0, net * 5.0)
            for code, name in full_sec["tickers"]:
                if code in pool:
                    continue  # yang eksplisit lebih diutamakan
                pool[code] = {
                    "score": fallback_score,
                    "count": sec["count"],
                    "code": code,
                    "name": name,
                    "sector": sec_key,
                    "sector_name": sec["name"],
                }
        # 3) vote pendorong pasar (suku bunga, emas, komoditas, perang, bitcoin)
        #     — hanya untuk horizon pendek & menengah.
        if h in ("short", "medium"):
            for code, v in driver_votes.items():
                cur = pool.get(code)
                if cur is None or v["score"] > cur["score"]:
                    pool[code] = dict(v)
        ranked = sorted(pool.values(), key=lambda x: -x["score"])
        # terapkan ambang skor minimal
        ranked = [v for v in ranked if v["score"] >= config.RECOMMENDATION_MIN_SCORE]
        for v in ranked[: config.TOP_RECOMMENDATIONS]:
            recs.append({
                "horizon": h,
                "code": v["code"],
                "name": v["name"],
                "sector": v["sector"],
                "sector_name": v.get("sector_name", v["sector"]),
                "score": round(v["score"], 3),
                "article_count": v["count"],
            })
    db.save_recommendations(day, recs)

    return signals


def _build_summary(s):
    parts = []
    if s["bull"]:
        parts.append(f"{len(s['bull'])} berita mendukung (bullish)")
    if s["bear"]:
        parts.append(f"{len(s['bear'])} berita menekan (bearish)")
    return "; ".join(parts) or "Belum ada sinyal kuat"


def run_pipeline(fetch=True, db=None, save_articles=True):
    """
    Menjalankan siklus penuh. Mengembalikan dict ringkasan.
    """
    db = db or dbmod.Database()
    day = today_str()
    errors = {}
    fetched = 0
    new_articles = 0

    articles = None
    if fetch:
        articles, errors = fetch_all()
        fetched = len(articles)
        if save_articles:
            for a in articles:
                analysis = classify_article(a)
                if db.insert_article(a, analysis):
                    new_articles += 1

    # Agregasi selalu memakai seluruh artikel pada hari ini (dari DB) agar
    # sinyal sebelumnya tidak terhapus saat fetch gagal (offline), dan agar
    # berita yang baru diambil ikut masuk.
    articles = db.recent_articles(after_date=day, limit=2000)
    articles = [a for a in articles if (a.get("published") or "")[:10] == day]

    signals = aggregate_day(db, day=day, articles=articles)
    db.set_meta("last_run", now_wib().isoformat())
    db.set_meta("last_run_day", day)

    _, driver_summary = build_driver_votes(db)

    return {
        "day": day,
        "fetched": fetched,
        "new_articles": new_articles,
        "signals": len(signals),
        "drivers": driver_summary,
        "errors": errors,
    }
