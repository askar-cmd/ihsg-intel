# -*- coding: utf-8 -*-
"""
Mesin proyeksi STRUKTURAL jangka panjang (1–10 tahun).

Berbeda dari rekomendasi harian yang berbasis berita langsung, mesin ini
melihat tema-tema transformatif yang berlangsung bertahun-tahun (mis. transisi
BBM → listrik, energi terbarukan, AI/digitalisasi, demografi, infrastruktur).

Cara kerja:
  1. Untuk setiap tema struktural (lihat config.STRUCTURAL_THEMES), kumpulkan
     berita terbaru yang menyentuh kata kunci tema.
  2. Hitung "momentum" dari sentimen bersih berita tsb (menunjukkan seberapa
     hangat/kuat tren kini).
  3. Skor akhir per saham = keyakinan dasar tema × bobot sektor × (1 + momentum),
     khusus untuk sektor yang diuntungkan (direction = +1).
  4. Hasilnya menjadi isi rekomendasi jangka panjang.
"""
import math
from datetime import datetime, timedelta

import config

_THEME_KEYWORDS = None


def _theme_keywords():
    global _THEME_KEYWORDS
    if _THEME_KEYWORDS is None:
        _THEME_KEYWORDS = [
            set(t["keywords"]) for t in config.STRUCTURAL_THEMES
        ]
    return _THEME_KEYWORDS


def _matches(article, keywords):
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    return any(k.lower() in text for k in keywords)


def _recent_articles(db, days):
    today = datetime.now().strftime("%Y-%m-%d")
    # simpan rentang via filter di Python (setelah ambil banyak)
    arts = db.recent_articles(limit=2000)
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [a for a in arts if (a.get("published") or "")[:10] >= cutoff]


def evaluate_themes(db, days=30):
    """
    Mengembalikan daftar tema beserta momentum & ringkasan.
    """
    arts = _recent_articles(db, days)
    out = []
    for theme in config.STRUCTURAL_THEMES:
        matches = [a for a in arts if _matches(a, theme["keywords"])]
        net = 0.0
        for a in matches:
            try:
                import json
                an = json.loads(a.get("analysis_json") or "{}")
                net += an.get("sentiment", 0.0)
            except Exception:
                continue
        momentum = math.tanh(net / max(1, len(matches))) if matches else 0.0
        out.append({
            "id": theme["id"],
            "name": theme["name"],
            "description": theme.get("description", ""),
            "articles": len(matches),
            "net_sentiment": round(net, 3),
            "momentum": round(momentum, 3),
        })
    return out


def build_long_recommendations(db, days=30, min_score=0.4):
    """
    Menghasilkan rekomendasi jangka panjang dari tema struktural.
    Mengembalikan (recs, theme_summary).
    """
    arts = _recent_articles(db, days)
    themes_out = evaluate_themes(db, days)
    momentum_map = {t["id"]: t["momentum"] for t in themes_out}
    count_map = {t["id"]: t["articles"] for t in themes_out}

    pooled = {}  # (code,theme_id) -> vote
    for theme in config.STRUCTURAL_THEMES:
        momentum = momentum_map.get(theme["id"], 0.0)
        base = theme.get("base_conviction", 1.0)
        # cukup biarkan tema yang punya cukup pijakan/momentum? Tapi base sudah
        # kuat, jadi tetap muncul; momentum hanya menaikkan/menurunkan sedikit.
        for sig in theme["signals"]:
            if sig.get("direction", 1) < 0:
                continue  # abai sektor yang tertekan
            sec_key = sig["sector"]
            w = sig.get("weight", 1.0)
            sec = config.SECTORS.get(sec_key)
            if not sec:
                continue
            # Jika sinyal menyebut daftar ticker spesifik, pakai itu;
            # jika tidak, gunakan seluruh ticker sektor.
            if sig.get("tickers"):
                tick_iter = [(c, config.STOCKS[c]["name"] if c in config.STOCKS else c)
                             for c in sig["tickers"]]
            else:
                tick_iter = sec["tickers"]
            eff = base * w * (1.0 + 0.6 * momentum)
            for code, name in tick_iter:
                key = (code, theme["id"])
                v = pooled.get(key)
                if v is None:
                    v = {"score": 0.0, "count": 0, "name": name,
                         "sector": sec_key, "sector_name": sec["name"],
                         "theme": theme["name"], "theme_id": theme["id"]}
                    pooled[key] = v
                v["score"] += eff
                v["count"] += count_map.get(theme["id"], 0)

    # aggregasi per kode: ambil tema dengan skor terbaik
    best = {}
    for (code, tid), v in pooled.items():
        cur = best.get(code)
        if cur is None or v["score"] > cur["score"]:
            best[code] = v

    recs = []
    for code, v in best.items():
        if v["score"] >= min_score:
            recs.append({
                "horizon": "long",
                "code": code,
                "name": v["name"],
                "sector": v["sector"],
                "sector_name": v["sector_name"],
                "score": round(v["score"], 3),
                "article_count": v["count"],
                "theme": v["theme"],
                "source": "struktural",
            })
    recs.sort(key=lambda r: -r["score"])
    return recs, themes_out


def theme_sectors_stocks(theme):
    """
    Mengembalikan daftar sektor & saham yang terkait dengan satu tema
    (berdasarkan config.STRUCTURAL_THEMES signals).
    """
    result = []
    seen_codes = set()
    for sig in theme.get("signals", []):
        if sig.get("direction", 1) < 0:
            continue  # abai sektor yang tertekan
        sec_key = sig["sector"]
        sec = config.SECTORS.get(sec_key)
        if not sec:
            continue
        # tentukan ticker yang terkait
        if sig.get("tickers"):
            tick_list = [(c, config.STOCKS[c]["name"] if c in config.STOCKS else c)
                         for c in sig["tickers"]]
        else:
            tick_list = sec["tickers"]
        stocks = []
        for code, name in tick_list:
            if code in seen_codes:
                continue
            seen_codes.add(code)
            stocks.append({"code": code, "name": name})
        result.append({
            "sector": sec_key,
            "sector_name": sec["name"],
            "weight": sig.get("weight", 1.0),
            "stocks": stocks,
        })
    return result


def theme_articles(db, theme_id, days=30):
    """Mengembalikan artikel yang cocok dengan satu tema."""
    theme = next((t for t in config.STRUCTURAL_THEMES if t["id"] == theme_id), None)
    if not theme:
        return []
    arts = _recent_articles(db, days)
    return [a for a in arts if _matches(a, theme["keywords"])]
