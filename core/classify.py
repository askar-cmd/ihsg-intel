# -*- coding: utf-8 -*-
"""
Mesin klasifikasi berita:
1. Sentimen (leksikon dwibahasa + pemeriksaan negasi & penguat).
2. Deteksi sektor yang terdampak (pemetaan kata kunci).
3. Kategori berita -> horizon waktu dampak (heuristik).
"""
import re
from collections import defaultdict

import config
from core.lexicon import (POSITIVE_ID, NEGATIVE_ID, POSITIVE_EN, NEGATIVE_EN,
                          NEGATION_WORDS, INTENSIFIERS)

# gabungkan leksikon
POSITIVE = set(POSITIVE_ID + POSITIVE_EN)
NEGATIVE = set(NEGATIVE_ID + NEGATIVE_EN)
NEGATION = set(NEGATION_WORDS)


def _tokenize(text):
    """Tokenisasi huruf kecil, token multikata (ngram 1-3)."""
    if not text:
        return []
    text = text.lower()
    # pertahankan frasa seperti "suku bunga" / "harga minyak" via ngram
    words = re.findall(r"[a-z0-9]+", text)
    tokens = list(words)
    for n in (2, 3):
        for i in range(len(words) - n + 1):
            tokens.append(" ".join(words[i:i + n]))
    return tokens


def sentiment_score(text):
    """
    Menghitung skor sentimen dalam rentang [-1, 1].
    Menggunakan leksikon; menangani negasi (dalam 2 token) & penguat.
    """
    tokens = _tokenize(text)
    score = 0.0
    weight = 0.0
    for i, tok in enumerate(tokens):
        base = 0
        if tok in POSITIVE:
            base = 1
        elif tok in NEGATIVE:
            base = -1
        if base == 0:
            continue
        # cek negasi dalam 2 token sebelumnya
        negated = False
        for j in range(max(0, i - 2), i):
            if tokens[j] in NEGATION or tokens[j] == "tidak":
                negated = True
                break
        mult = 1.0
        # cek penguat tepat sebelum
        if i > 0 and tokens[i - 1] in INTENSIFIERS:
            mult = INTENSIFIERS[tokens[i - 1]]
        contrib = base * mult
        if negated:
            contrib = -contrib
        score += contrib
        weight += 1.0
    if weight == 0:
        return 0.0
    # normalisasi ke [-1, 1] dengan tanh
    import math
    norm = score / (weight + 2.0)
    return round(math.tanh(norm * 3.0), 4)


def detect_sectors(text):
    """Mengembalikan set kode sektor yang disebut dalam teks + kata yang cocok."""
    tokens = set(_tokenize(text))
    matched = {}
    for sec_key, sec in config.SECTORS.items():
        hits = [k for k in sec["keywords"] if k in tokens]
        if hits:
            matched[sec_key] = hits
    return matched


def detect_category(text):
    """Menentukan kategori berita dominan; mengembalikan kode kategori atau None."""
    tokens = set(_tokenize(text))
    best = None
    best_hits = 0
    for cat_key, cat in config.CATEGORIES.items():
        hits = [k for k in cat["keywords"] if k in tokens]
        if len(hits) > best_hits:
            best_hits = len(hits)
            best = cat_key
    return best


def _ticker_mentioned(text, code, name):
    """
    Benar jika sebuah saham benar-benar disebut dalam teks artikel.
    Cocokkan kode (case-insensitive, batas kata) atau nama perusahaan.
    Ini membuat filter per-saham akurat, tidak "menyeret" seluruh sektor.
    """
    if not code:
        return False
    upper = text.upper()
    if re.search(r"\b" + re.escape(code.upper()) + r"\b", upper):
        return True
    if name and name.lower() in text.lower():
        return True
    return False


def classify_article(article):
    """
    Memproses satu artikel -> dict hasil analisis.
    """
    text = f"{article.get('title','')}. {article.get('summary','')}"
    sent = sentiment_score(text)

    sectors = detect_sectors(text)
    cat_key = detect_category(text)
    cat = config.CATEGORIES.get(cat_key) if cat_key else None

    # Horizon waktu dari kategori; jika tidak ada kategori, default medium
    if cat:
        horizons = cat["horizons"]
    else:
        horizons = ["medium"]

    # Arah: sentimen -> bullish/bearish
    label = "netral"
    if sent >= config.SENTIMENT_THRESHOLD:
        label = "bullish"
    elif sent <= -config.SENTIMENT_THRESHOLD:
        label = "bearish"

    # Sektor terdampak + ticker yang BENAR-BENAR disebut dalam artikel
    affected = {}
    for sec_key, hits in sectors.items():
        sec = config.SECTORS[sec_key]
        tickers = [
            {"code": c, "name": n, "sector": sec_key}
            for c, n in sec["tickers"] if _ticker_mentioned(text, c, n)
        ]
        weight = 1.0
        if cat:
            weight = cat["sector_weight"]
        affected[sec_key] = {
            "name": sec["name"],
            "hit_keywords": hits,
            "tickers": tickers,
            "weight": weight,
            "direction": label,
        }

    return {
        "sentiment": sent,
        "label": label,
        "category": cat_key,
        "category_name": cat["name"] if cat else "Umum / Tidak terklasifikasi",
        "horizons": horizons,
        "horizon_labels": [config.HORIZONS[h]["label"] for h in horizons],
        "sectors": affected,
    }
