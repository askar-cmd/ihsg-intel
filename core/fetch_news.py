# -*- coding: utf-8 -*-
"""
Pengambil & pembersih berita dari RSS.
Mendukung deduplikasi, normalisasi ringkas, dan penandaan sumber.
"""
import re
import sys
import time
import hashlib
from datetime import datetime, timezone
from collections import OrderedDict

try:
    import feedparser
except Exception:  # pragma: no cover
    feedparser = None

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

import config


def _clean_html(text):
    """Buang tag HTML & galat kode, normalisasi spasi."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&#39;|&quot;|&ldquo;|&rdquo;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _published_dt(entry):
    """Coba ambil waktu terbit dari RSS, fallback ke sekarang."""
    for attr in ("published_parsed", "updated_parsed"):
        sp = entry.get(attr)
        if sp:
            try:
                return datetime(*sp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def fetch_html_list(src, user_agent=None):
    """
    Scraper ringan untuk halaman daftar berita (bukan RSS).
    Mengekstrak pasangan (judul, tautan) dari tag <a> pada halaman.
    Bersifat best-effort: jika gagal, mengembalikan [{"error": ...}].
    """
    if requests is None:
        return [{"error": "requests tidak terpasang"}]
    url = src["url"]
    headers = {
        "User-Agent": user_agent or config.USER_AGENT,
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        return [{"error": str(exc)}]

    # ekstrak anchor: href > title
    anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                         html, flags=re.I | re.S)
    articles = []
    seen = set()
    base = re.match(r'(https?://[^/]+)', url)
    base = base.group(1) if base else ""
    for href, title in anchors:
        title = _clean_html(title)
        if len(title) < 20:
            continue
        # hanya tautan artikel (hindari nav/footer)
        if not href or "javascript" in href.lower():
            continue
        link = href if href.startswith("http") else (base + href if href.startswith("/") else url)
        # buang yang jelas bukan artikel
        if any(x in link.lower() for x in ("/rss", "javascript", "#", "/category", "/search")):
            continue
        key = hashlib.md5(title.lower().encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        articles.append({
            "source_id": src["id"],
            "source_name": src["name"],
            "country": src["country"],
            "lang": src["lag"],
            "title": title[:400],
            "summary": "",
            "link": link[:600],
            "published": datetime.now(timezone.utc),
            "fingerprint": key,
        })
        if len(articles) >= config.MAX_ARTICLES_PER_SOURCE:
            break
    return articles if articles else [{"error": "tidak ada artikel terdeteksi"}]


def fetch_source(src, user_agent=None):
    """Mengambil & mem-parsing satu sumber (RSS atau HTML list). Mengembalikan daftar article dict."""
    if src.get("type") == "html_list":
        return fetch_html_list(src, user_agent=user_agent)
    if feedparser is None:
        return []
    headers = {"User-Agent": user_agent or config.USER_AGENT}
    try:
        parsed = feedparser.parse(src["url"], request_headers=headers)
    except Exception as exc:
        return [{"error": str(exc)}]

    if parsed.get("bozo") and not parsed.get("entries"):
        return [{"error": f"feed tidak valid: {parsed.get('bozo_exception')}"}]

    articles = []
    seen = set()
    for entry in parsed.entries[: config.MAX_ARTICLES_PER_SOURCE]:
        title = _clean_html(entry.get("title", ""))
        if not title:
            continue
        link = entry.get("link", "")
        summary = _clean_html(entry.get("summary", "") or entry.get("description", ""))
        key = hashlib.md5(title.lower().encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        articles.append({
            "source_id": src["id"],
            "source_name": src["name"],
            "country": src["country"],
            "lang": src["lag"],
            "title": title[:400],
            "summary": summary[:1200],
            "link": link,
            "published": _published_dt(entry),
            "fingerprint": key,
        })
    return articles


def fetch_all(sources=None, user_agent=None):
    """Mengambil semua sumber; mengembalikan (articles, errors)."""
    sources = sources or config.SOURCES
    all_articles = []
    errors = {}
    for src in sources:
        try:
            res = fetch_source(src, user_agent=user_agent)
            for item in res:
                if "error" in item:
                    errors[src["id"]] = item["error"]
                else:
                    all_articles.append(item)
        except Exception as exc:
            errors[src["id"]] = str(exc)
        time.sleep(0.3)
    # deduplikasi lintas sumber berdasarkan judul
    unique = OrderedDict()
    for a in all_articles:
        unique.setdefault(a["fingerprint"], a)
    return list(unique.values()), errors
