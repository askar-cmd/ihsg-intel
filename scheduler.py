# -*- coding: utf-8 -*-
"""
Penjadwal otomatis. Menggunakan APScheduler.

Perilaku:
  1. Pembaruan langsung ~beberapa detik setelah server menyala
     (saat komputer online, berita langsung diambil).
  2. Pembaruan berulang setiap 1 jam selama komputer (aplikasi) aktif.

Bisa dimatikan seluruhnya dengan env DISABLE_SCHEDULER=1.
"""
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

import config
from core.analyzer import run_pipeline

_scheduler = None


def _job():
    try:
        summary = run_pipeline(fetch=True)
        print(f"[scheduler] siklus selesai: {summary}")
    except Exception as exc:
        print(f"[scheduler] error: {exc}")


def _price_job():
    """Sinkronkan harga + evaluasi akurasi prediksi (sekali sehari)."""
    try:
        from core.learn import evaluate_recommendations, sync_prices_for_tickers
        from core.db import Database
        d = Database()
        recs = d.all_recommendations()
        codes = sorted({r["code"] for r in recs})
        if codes:
            sync_prices_for_tickers(d, codes)
        summary = evaluate_recommendations(d)
        print("[scheduler] evaluasi prediksi:", summary)
    except Exception as exc:
        print(f"[scheduler] error evaluasi prediksi: {exc}")


def start_scheduler():
    """Memulai scheduler background (idempotent)."""
    global _scheduler
    if os.environ.get("DISABLE_SCHEDULER") == "1":
        return None
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone=config.TIMEZONE)

    # 1) pembaruan pertama segera setelah server hidup
    run_at = datetime.now() + timedelta(seconds=config.FIRST_UPDATE_DELAY_SECONDS)
    _scheduler.add_job(_job, "date", run_date=run_at,
                       id="first_update", replace_existing=True)

    # 2) pembaruan berulang setiap 1 jam selama aplikasi aktif
    _scheduler.add_job(_job, IntervalTrigger(hours=config.UPDATE_INTERVAL_HOURS),
                       id="hourly_update", replace_existing=True)

    # 3) evaluasi prediksi + sinkronisasi harga harian (default 17:05 SGT)
    _scheduler.add_job(_price_job, CronTrigger(
        hour=config.PRICE_CHECK_HOUR, minute=config.PRICE_CHECK_MINUTE,
        timezone=config.TIMEZONE), id="daily_price_check", replace_existing=True)

    _scheduler.start()
    return _scheduler


def shutdown():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
