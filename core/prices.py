# -*- coding: utf-8 -*-
"""
Pengambil harga saham harian (riwayat). Menggunakan endpoint chart Yahoo Finance
yang gratis dan tanpa kunci API. Kode saham IDX diberi akhiran ".JK".

Contoh: ACES -> ACES.JK
"""
from datetime import datetime, timezone

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

import config

_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"


def fetch_price_history(code, days=None):
    """
    Mengembalikan daftar {date, open, high, low, close, volume} diurutkan naik.
    Kosong jika gagal (offline / kode tidak ditemukan).
    """
    if requests is None:
        return []
    days = days or config.PRICE_HISTORY_DAYS
    sym = code.upper() + ".JK"
    try:
        resp = requests.get(
            _BASE + requests.utils.quote(sym),
            params={
                "range": f"{days}d",
                "interval": "1d",
                "includePrePost": "false",
                "events": "history",
            },
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        data = resp.json()
        res = data["chart"]["result"][0]
        ts = res.get("timestamp") or []
        q = res["indicators"]["quote"][0]
        closes = q.get("close") or []
        opens = q.get("open") or []
        highs = q.get("high") or []
        lows = q.get("low") or []
        vols = q.get("volume") or []

        rows = []
        for i, t in enumerate(ts):
            c = closes[i] if i < len(closes) else None
            if c is None:
                continue
            rows.append({
                "date": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"),
                "open": opens[i] if i < len(opens) else c,
                "high": highs[i] if i < len(highs) else c,
                "low": lows[i] if i < len(lows) else c,
                "close": c,
                "volume": vols[i] if i < len(vols) else None,
            })
        return rows
    except Exception as exc:
        return []
