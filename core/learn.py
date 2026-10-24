# -*- coding: utf-8 -*-
"""
Mekanisme "belajar dari pengalaman":
1. Memantau harga saham yang masuk rekomendasi (via / core.prices).
2. Membandingkan prediksi (bullish) dengan pergerakan harga nyata.
3. Memperbarui bobot per sektor/horizon berdasarkan akurasi riwayat.
4. Bobot hasil belajar dipakai ulang untuk analisis berikutnya
   (lihat core.analyzer.aggregate_day).

Logika belajar sederhana (heuristik):
  - Akurasi > 50%  -> bobot dinaikkan (sampai 2.0x)
  - Akurasi < 50%  -> bobot diturunkan (sampai 0.3x)
  - Kurang contoh (total < MODEL_MIN_SAMPLES) -> bobot netral 1.0
"""
import config
from core import db as dbmod
from core.prices import fetch_price_history


def get_model_weights(db):
    """
    Mengembalikan dict {(horizon, sector): multiplier}.
    multiplier dipakai untuk mengalikan bobot sektor saat penilaian.
    """
    weights = {}
    fb = db.model_feedback_all()
    for row in fb:
        h = row["horizon"]
        s = row["sector"]
        total = row["total"]
        correct = row["correct"]
        if total < config.MODEL_MIN_SAMPLES:
            weights[(h, s)] = 1.0
            continue
        acc = correct / total
        # baseline 1.0, variasikan ± hingga x2
        mult = 1.0 + (acc - 0.5) * 2.0
        mult = max(0.3, min(2.0, mult))
        weights[(h, s)] = round(mult, 3)
    return weights


def sync_prices_for_tickers(db, tickers, days=None):
    """Unduh riwayat harga untuk daftar ticker lalu simpan ke cache."""
    saved = 0
    for tk in tickers:
        if not tk:
            continue
        rows = fetch_price_history(tk, days=days)
        if rows:
            db.upsert_prices(tk, rows)
            saved += 1
    return saved


def _entry_price(db, rec_date, code):
    """Harga penutupan pertama tersedia pada/lewat tanggal rekomendasi."""
    px = db.get_prices(code)
    if not px:
        return None
    for p in px:
        if p["date"] >= rec_date:
            return p["close"]
    return px[0]["close"]  # belum ada data setanggal itu -> pakai data terawal


def evaluate_recommendations(db, min_recency_days=0):
    """
    Mengevaluasi rekomendasi masa lalu terhadap harga terkini dan
    memperbarui feedback model.

    Mengembalikan dict ringkasan.
    """
    recs = db.all_recommendations()
    if not recs:
        return {"evaluated": 0, "skipped": 0, "codes": 0}

    # pastikan harga untuk semua kode yang direkomendasikan tersedia
    tickers = sorted({r["code"] for r in recs})
    missing = [tk for tk in tickers if not db.price_latest(tk)]
    if missing:
        sync_prices_for_tickers(db, missing)

    evaluated = 0
    skipped = 0
    for r in recs:
        if db.performance_exists(r["date"], r["horizon"], r["code"]):
            skipped += 1
            continue
        entry = _entry_price(db, r["date"], r["code"])
        cur = db.price_latest(r["code"])
        if entry is None or cur is None or cur.get("close") is None:
            continue
        pct = (cur["close"] - entry) / entry if entry else 0.0
        outcome = "menang" if pct > 0.001 else ("kalah" if pct < -0.001 else "netral")
        db.save_performance({
            "date": r["date"],
            "horizon": r["horizon"],
            "code": r["code"],
            "name": r.get("name", ""),
            "sector": r.get("sector", ""),
            "sector_name": r.get("sector_name", ""),
            "entry_price": entry,
            "current_price": cur["close"],
            "pct_change": round(pct * 100, 2),
            "signal_dir": "bullish",
            "outcome": outcome,
        })
        db.bump_feedback(r["horizon"], r["sector"], outcome == "menang")
        evaluated += 1

    summary = model_summary(db)
    summary["evaluated"] = evaluated
    summary["skipped"] = skipped
    summary["codes"] = len(tickers)

    # catat waktu terakhir prediksi diperbarui (dalam zona waktu SGT, +8)
    try:
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo
            sgt = ZoneInfo("Asia/Singapore")
        except Exception:
            from datetime import timezone, timedelta
            sgt = timezone(timedelta(hours=8))
        db.set_meta("last_prediction_update",
                    datetime.now(sgt).isoformat())
    except Exception:
        pass
    return summary


def _is_flat_series(series, window=10):
    """
    Benar jika N harga penutupan terakhir semuanya identik (tidak bergerak),
    yang mengindikasikan saham suspend / tidak aktif diperdagangkan.
    """
    if not series or len(series) < window:
        return False
    closes = [p.get("close") for p in series[-window:]]
    if any(c is None for c in closes):
        return False
    first = closes[0]
    return all(abs(c - first) < 1e-9 for c in closes)


def filter_active_recommendations(db, recs, window=10):
    """
    Menyaring rekomendasi: buang saham yang terdeteksi suspend (harga flat).
    Mengembalikan (active_recs, suspended_list).
    """
    active = {}
    suspended = []
    for h, items in (recs or {}).items():
        keep = []
        for r in items:
            series = db.get_prices(r["code"])
            if _is_flat_series(series, window):
                suspended.append({
                    "code": r["code"],
                    "name": r.get("name", ""),
                    "sector_name": r.get("sector_name", r.get("sector", "")),
                    "horizon": h,
                })
            else:
                keep.append(r)
        if keep:
            active[h] = keep
    return active, suspended


def model_summary(db):
    """Ringkasan akurasi model + bobot hasil belajar."""
    fb = db.model_feedback_all()
    by_horizon = {}
    details = []
    for row in fb:
        h = row["horizon"]
        acc = round(row["correct"] / row["total"], 3) if row["total"] else 0.0
        by_horizon.setdefault(h, {"correct": 0, "total": 0})
        by_horizon[h]["correct"] += row["correct"]
        by_horizon[h]["total"] += row["total"]
        details.append({
            "horizon": h,
            "sector": row["sector"],
            "correct": row["correct"],
            "total": row["total"],
            "accuracy": acc,
        })
    summary = {"details": details, "horizons": {}}
    for h, v in by_horizon.items():
        summary["horizons"][h] = {
            "accuracy": round(v["correct"] / v["total"], 3) if v["total"] else 0.0,
            "total": v["total"],
            "correct": v["correct"],
        }
    return summary
