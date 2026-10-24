# -*- coding: utf-8 -*-
"""
Mesin Pendorong Pasar (Market Drivers) — faktor makro yang memengaruhi
pergerakan saham: suku bunga, harga emas, komoditas, geopolitik/perang,
dan Bitcoin/kripto.

Setiap driver mencocokkan berita terbaru, menghitung sentimen bersih, lalu
memetakan arahnya ke sektor/saham yang diuntungkan (lihat
config.MARKET_DRIVERS). Hasilnya disuntikkan ke rekomendasi pendek/menengah
sebagai "vote" tambahan.
"""
import math

import config


def _matches(article, keywords):
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    return any(k.lower() in text for k in keywords)


def evaluate_drivers(db, days=14):
    """
    Menilai setiap driver dari berita terbaru.
    Mengembalikan daftar {id, name, notes, articles, net_sentiment, momentum,
                           mood, direction}.
    """
    arts = db.recent_articles(limit=2000)
    out = []
    for drv in config.MARKET_DRIVERS:
        matches = [a for a in arts if _matches(a, drv["keywords"])]
        net = 0.0
        for a in matches:
            try:
                import json
                an = json.loads(a.get("analysis_json") or "{}")
                net += an.get("sentiment", 0.0)
            except Exception:
                continue
        momentum = math.tanh(net / max(1, len(matches))) if matches else 0.0
        # mood: arah yang menguntungkan (bullish 1 / bearish -1)
        mood = "netral"
        if momentum >= 0.15:
            mood = "bullish" if drv.get("direction", 1) > 0 else "bearish"
        elif momentum <= -0.15:
            mood = "bearish" if drv.get("direction", 1) > 0 else "bullish"
        out.append({
            "id": drv["id"],
            "name": drv["name"],
            "notes": drv.get("notes", ""),
            "articles": len(matches),
            "net_sentiment": round(net, 3),
            "momentum": round(momentum, 3),
            "mood": mood,
            "direction": drv.get("direction", 1),
        })
    return out


def build_driver_votes(db, days=14):
    """
    Mengubah momentum driver menjadi "vote" per ticker (sektor yang diuntungkan).
    Mengembalikan (votes, drivers) dengan votes = {code: {score, count, ...}}.
    """
    drivers = evaluate_drivers(db, days)
    votes = {}
    for drv, info in zip(config.MARKET_DRIVERS, drivers):
        momentum = info["momentum"]
        if abs(momentum) < 0.12:
            continue  # tidak cukup sinyal
        # pilih daftar sektor berdasarkan arah
        target = ("bullish" if momentum > 0 else "bearish")
        if info.get("direction", 1) < 0:
            target = "bearish" if momentum > 0 else "bullish"
        sector_list = drv.get(target) or []
        # skor dasar sebanding dengan kekuatan momentum
        base = abs(momentum) * 2.0
        for item in sector_list:
            sec_key = item["sector"]
            sec = config.SECTORS.get(sec_key)
            if not sec:
                continue
            w = item.get("weight", 1.0)
            if item.get("tickers"):
                tick_iter = [(c, config.STOCKS[c]["name"] if c in config.STOCKS else c)
                             for c in item["tickers"]]
            else:
                tick_iter = sec["tickers"]
            for code, name in tick_iter:
                v = votes.get(code)
                if v is None:
                    v = {"score": 0.0, "count": 0, "name": name,
                         "sector": sec_key, "sector_name": sec["name"],
                         "driver": drv["name"], "driver_id": drv["id"]}
                    votes[code] = v
                v["score"] += base * w
                v["count"] += info["articles"]
    return votes, drivers
