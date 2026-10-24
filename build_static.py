# -*- coding: utf-8 -*-
"""
Membangun versi statis dashboard untuk GitHub Pages.

Menjalankan satu siklus pipeline (ambil berita + analisis), evaluasi prediksi
harian bila sudah waktunya, lalu menyimpan setiap respons API sebagai file JSON
sehingga dashboard bisa disajikan tanpa server Python.

Jalankan:
    python build_static.py                 # hasil di folder _site/
    python build_static.py --no-fetch      # tanpa mengambil berita baru
    python build_static.py --check         # paksa evaluasi prediksi sekarang
"""
import argparse
import asyncio
import gzip
import json
import os
import shutil
import sys

os.environ["DISABLE_SCHEDULER"] = "1"
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import config  # noqa: E402
import main  # noqa: E402  (fungsi endpoint dipakai ulang apa adanya)
from core.analyzer import run_pipeline, now_wib  # noqa: E402
from core.learn import evaluate_recommendations, sync_prices_for_tickers  # noqa: E402

STATIC_DIR = os.path.join(ROOT, "static")


def call(endpoint, **kwargs):
    return asyncio.run(endpoint(**kwargs))


def write_json(out, rel, data):
    path = os.path.join(out, "api", rel + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str, separators=(",", ":"))


def price_check_due(db):
    """Evaluasi prediksi sekali sehari, setelah jam PRICE_CHECK_HOUR (SGT)."""
    now = now_wib()
    if (now.hour, now.minute) < (config.PRICE_CHECK_HOUR, config.PRICE_CHECK_MINUTE):
        return False
    last = db.get_meta("last_prediction_update") or ""
    return last[:10] != now.strftime("%Y-%m-%d")


def run_price_check(db):
    """Sama dengan scheduler._price_job: sinkron harga + evaluasi akurasi."""
    codes = sorted({r["code"] for r in db.all_recommendations()})
    if codes:
        sync_prices_for_tickers(db, codes)
    return evaluate_recommendations(db)


def news_for(**flt):
    args = dict(limit=50, date=None, ticker=None, sector=None, driver=None)
    args.update(flt)
    return call(main.news, **args)


def build(out):
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)

    write_json(out, "config", call(main.api_config))
    write_json(out, "health", call(main.health))
    write_json(out, "dashboard", call(main.dashboard))
    write_json(out, "prices", call(main.prices))
    write_json(out, "model", call(main.model))

    for t in config.STRUCTURAL_THEMES:
        write_json(out, f"themes/{t['id']}", call(main.theme_detail, theme_id=t["id"]))
    for code in config.STOCKS:
        write_json(out, f"news/ticker/{code}", news_for(ticker=code))
    for key in config.SECTORS:
        write_json(out, f"news/sector/{key}", news_for(sector=key))
    for d in config.MARKET_DRIVERS:
        write_json(out, f"news/driver/{d['id']}", news_for(driver=d["id"]))

    # dashboard: path relatif + penanda mode statis untuk app.js
    with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
        html = f.read()
    html = html.replace('"/static/', '"static/').replace(
        '<meta charset="UTF-8">', '<meta charset="UTF-8">\n<meta name="static-site" content="1">', 1)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    shutil.copytree(STATIC_DIR, os.path.join(out, "static"),
                    ignore=shutil.ignore_patterns("index.html"))
    open(os.path.join(out, ".nojekyll"), "w").close()

    # salinan database agar run berikutnya bisa melanjutkan riwayat & belajar
    os.makedirs(os.path.join(out, "state"), exist_ok=True)
    with open(config.DB_PATH, "rb") as src, \
            gzip.open(os.path.join(out, "state", "pasar_intel.db.gz"), "wb") as dst:
        shutil.copyfileobj(src, dst)


def cli():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out", default="_site")
    ap.add_argument("--no-fetch", action="store_true", help="jangan ambil berita baru")
    ap.add_argument("--check", action="store_true", help="paksa evaluasi prediksi")
    args = ap.parse_args()

    db = main.db
    if not args.no_fetch:
        summary = run_pipeline(fetch=True, db=db)
        print("[build] siklus berita:", {k: v for k, v in summary.items() if k != "drivers"})
    if args.check or price_check_due(db):
        print("[build] evaluasi prediksi:", run_price_check(db))
    build(os.path.abspath(args.out))
    print("[build] selesai ->", args.out)


if __name__ == "__main__":
    cli()
