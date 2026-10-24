// Pasar Intel — frontend dashboard
(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => {
    if (s && typeof s === "object") {
      try { s = JSON.stringify(s); } catch (e) { s = String(s); }
    }
    return String(s ?? "").replace(/[&<>"']/g, c =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  };

  let HORIZONS = { short: "Pendek", medium: "Menengah", long: "Panjang" };
  let MIN_SCORE = 0.4;

  let ALL_NEWS = [];          // semua berita terbaru (tanpa filter)
  let FILTERED_NEWS = null;   // berita hasil filter; null = tidak difilter
  let newsFilter = null;      // { code, name }
  let PWATCH = [];            // data harga yang terpantau (untuk modal)
  let MODEL_DATA = null;      // data model + evaluasi (untuk panel detail)

  // Mode statis (GitHub Pages): data dibaca dari file JSON hasil build_static.py,
  // bukan dari server FastAPI. Ditandai oleh <meta name="static-site">.
  const STATIC = !!document.querySelector('meta[name="static-site"]');

  // apiUrl("news", {ticker: "BBRI"}) -> "/api/news?ticker=BBRI"
  //                             (statis) "api/news/ticker/BBRI.json"
  function apiUrl(path, params) {
    params = params || {};
    const nonce = params._ ? "?_=" + params._ : "";
    if (!STATIC) {
      const q = new URLSearchParams(params).toString();
      return "/api/" + path + (q ? "?" + q : "");
    }
    const filter = Object.entries(params).find(([k]) => k !== "_");
    const sub = filter ? `/${filter[0]}/${encodeURIComponent(filter[1])}` : "";
    return "api/" + path + sub + ".json" + nonce;
  }

  function hzLabel(k) { return HORIZONS[k] || k; }

  // Ubah tanggal ISO "YYYY-MM-DD" -> "DD-MM-YYYY"
  function fmtDate(iso) {
    const p = String(iso || "").split(" ")[0].split("-");
    return p.length === 3 ? `${p[2]}-${p[1]}-${p[0]}` : (iso || "");
  }

  // Ubah timestamp ISO (mis. "2026-10-21T08:15:48+07:00") -> "DD-MM-YYYY HH:MM"
  function fmtDateTime(iso) {
    if (!iso) return "–";
    const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
    if (!m) return iso;
    return `${m[3]}-${m[2]}-${m[1]} ${m[4]}:${m[5]}`;
  }

  function sentimentPill(label) {
    const map = { bullish: "Bullish ▲", bearish: "Bearish ▼", netral: "Netral —" };
    return `<span class="pill ${esc(label)}">${esc(map[label] || label)}</span>`;
  }

  async function loadConfig() {
    try {
      const r = await fetch(apiUrl("config"));
      const d = await r.json();
      if (d.horizons) {
        // API mengirim {short:{label,range},...}; simpan hanya label teks.
        const lbl = {};
        for (const k in d.horizons) {
          const v = d.horizons[k];
          lbl[k] = (v && typeof v === "object") ? (v.label || k) : v;
        }
        HORIZONS = lbl;
      }
      if (d.recommendation_min_score != null) MIN_SCORE = d.recommendation_min_score;
    } catch (e) { /* abaikan */ }
  }

  function renderSummary(d) {
    const t = d.totals || {};
    const by = t.by_label || {};
    const last = d.recent_news || [];
    const bullish = by.bullish || 0, bearish = by.bearish || 0, netral = by.netral || 0;
    const total = t.articles || 0;
    const todaySignals = (d.signals || []).length;

    const cards = [
      { k: "Total Berita", v: total },
      { k: "Bullish", v: bullish, cls: "bullish" },
      { k: "Bearish", v: bearish, cls: "bearish" },
      { k: "Netral", v: netral },
      { k: "Sektor Bersinyal", v: todaySignals },
      { k: "Berita Terbaru", v: last.length },
    ];
    $("#summaryCards").innerHTML = cards.map(c => `
      <div class="card">
        <div class="k">${esc(c.k)}</div>
        <div class="v small ${esc(c.cls || "")}">${c.v}</div>
      </div>`).join("");
  }

  function renderMatrix(d) {
    const signals = d.signals || [];
    if (!signals.length) {
      $("#sectorMatrix").innerHTML = `<div class="empty">Belum ada data sinyal sektor.</div>`;
      return;
    }
    const rows = signals.map(s => {
      const cells = ["short", "medium", "long"].map(h => {
        const dir = s["direction_" + h];
        return `<div><span class="pill ${esc(dir)}">${esc(dir)}</span></div>`;
      }).join("");
      const tickers = (s.tickers || []).slice(0, 8).map(t => t.code).join(", ");
      return `
        <tr>
          <td>
            <button type="button" class="sec-link" data-filter-sector="${esc(s.sector)}" data-filter-name="${esc(s.name)}" title="Klik untuk melihat ${s.article_count} berita sektor">${esc(s.name)}</button>
            <div class="tickers">${esc(tickers)}</div>
          </td>
          <td class="hz-cell">${cells}</td>
          <td>${s.article_count}</td>
          <td style="color:var(--muted);font-size:12px">${esc(s.summary)}</td>
        </tr>`;
    }).join("");

    $("#sectorMatrix").innerHTML = `
      <table>
        <thead><tr>
          <th>Sektor</th><th>Dampak / Horizon</th><th>Jml Berita</th><th>Ringkasan</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  function renderRecommendations(d) {
    const recs = d.recommendations || {};
    const order = ["short", "medium", "long"];
    const labels = { short: "Pendek · 1–3 bln", medium: "Menengah · 3–12 bln", long: "Panjang · 1–10 thn" };
    const note = $("#recNote");
    if (note) {
      const susp = d.suspended || [];
      let txt = `(ambang skor ≥ ${MIN_SCORE})`;
      if (susp.length) {
        txt += ` · ${susp.length} saham dikeluarkan (suspend): ` +
               susp.map(s => s.code).join(", ");
      }
      note.textContent = txt;
    }

    if (!order.some(h => (recs[h] || []).length)) {
      $("#recommendations").innerHTML =
        `<div class="empty">Belum ada rekomendasi saham di atas ambang skor.</div>`;
      return;
    }

    const panels = order.map(h => {
      const list = recs[h] || [];
      const body = list.length
        ? list.map(r => `
            <button type="button" class="rec-item" data-filter-ticker="${esc(r.code)}" data-filter-name="${esc(r.name)}" title="Klik untuk melihat ${r.article_count} berita terkait">
              <div class="rec-code">${esc(r.code)} <span class="rec-cta">→</span></div>
              <div class="rec-name">${esc(r.name)}</div>
              <div class="rec-meta">${esc(r.sector_name || r.sector)} · ${r.article_count} berita</div>
              ${r.source === "struktural" ? `<div class="rec-theme">🧭 ${esc(r.theme)}</div>` : ""}
            </button>`).join("")
        : `<div class="rec-none">Tidak ada sinyal di atas ambang</div>`;
      return `
        <div class="rec-panel">
          <div class="rec-head">${esc(labels[h])}</div>
          <div class="rec-body">${body}</div>
        </div>`;
    }).join("");

    $("#recommendations").innerHTML = `<div class="rec-grid">${panels}</div>`;
  }

  function sparkline(series, W) {
    const closes = series.map(p => Number(p.close)).filter(v => !isNaN(v));
    if (closes.length < 2) return "";
    W = W || 236;
    const H = Math.round(W * 88 / 236);
    const mL = 56, mR = 8, mT = 12, mB = 16;
    const pw = W - mL - mR, ph = H - mT - mB;
    const n = closes.length;
    const min = Math.min(...closes), max = Math.max(...closes);
    const range = (max - min) || 1;
    const X = i => mL + i * pw / (n - 1);
    const Y = v => mT + (1 - v) * ph;
    const pts = closes.map((c, i) =>
      `${X(i).toFixed(1)},${Y((c - min) / range).toFixed(1)}`).join(" ");
    const up = closes[n - 1] >= closes[0];
    const color = up ? "var(--green)" : "var(--red)";
    const fmt = v => (v != null && !isNaN(Number(v)) ? Number(v).toLocaleString("id-ID") : "–");
    const shortDate = s => { const p = String(s).split("-"); return p.length >= 3 ? `${+p[2]}-${+p[1]}` : s; };

    // Tanda tanggal harian (sumbu-X): taruh sebanyak mungkin label agar tidak
    // saling tumpang tindih (±26px per label). Setiap titik hari tetap punya
    // tooltip tanggal & harga saat disentuh/hover (lihat loop titik di bawah).
    const labelStep = Math.max(1, Math.round(pw / 26));
    const idxs = [];
    for (let i = 0; i < n; i += labelStep) idxs.push(i);
    if (idxs[idxs.length - 1] !== n - 1) idxs.push(n - 1);

    const gridLines = idxs.map(idx => {
      const x = X(idx).toFixed(1);
      return `
        <line x1="${x}" y1="${mT}" x2="${x}" y2="${mT + ph}" stroke="var(--border)" stroke-width="1" stroke-dasharray="2 4" opacity="0.35"/>
        <text x="${x}" y="${H - 3}" font-size="8.5" fill="var(--muted)" text-anchor="middle">${shortDate(series[idx].date)}</text>`;
    }).join("");

    // Sumbu-Y (harga): beberapa garis horizontal dengan label harga di samping kiri.
    const priceTicks = 4;
    const priceAxis = [];
    for (let k = 0; k <= priceTicks; k++) {
      const val = min + (max - min) * k / priceTicks;
      const y = Y(k / priceTicks).toFixed(1);
      priceAxis.push(`
        <line x1="${mL}" y1="${y}" x2="${W - mR}" y2="${y}" stroke="var(--border)" stroke-width="1" stroke-dasharray="2 4" opacity="0.25"/>
        <text x="${mL - 6}" y="${+y + 3}" font-size="8.5" fill="var(--muted)" text-anchor="end">${fmt(Math.round(val))}</text>`);
    }

    // Satu titik tak terlihat per hari, masing-masing dengan tooltip asli
    // (tanggal & harga) — jadi setiap tanggal "harian" tetap bisa dibaca.
    const dayPoints = closes.map((c, i) => {
      const x = X(i).toFixed(1), y = Y((c - min) / range).toFixed(1);
      return `
        <circle cx="${x}" cy="${y}" r="4" fill="transparent">
          <title>${fmtDate(series[i].date)} · ${fmt(c)}</title>
        </circle>`;
    }).join("");

    return `<svg viewBox="0 0 ${W} ${H}" class="spark">
      <line x1="${mL}" y1="${mT + ph}" x2="${W - mR}" y2="${mT + ph}" stroke="var(--border)" stroke-width="1"/>
      ${priceAxis}
      ${gridLines}
      <text x="${W - mR}" y="${mT - 4}" font-size="9" fill="${color}" text-anchor="end" font-weight="600">${fmt(closes[n - 1])}</text>
      <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" vector-effect="non-scaling-stroke"/>
      ${dayPoints}
      <circle cx="${X(n - 1).toFixed(1)}" cy="${Y((closes[n - 1] - min) / range).toFixed(1)}" r="3" fill="${color}"/>
    </svg>`;
  }

  function renderDrivers(d) {
    const drivers = (d && d.drivers) || [];
    if (!drivers.length) {
      $("#driversList").innerHTML = `<div class="empty">Belum ada data pendorong pasar.</div>`;
      return;
    }
    const cards = drivers.map(v => {
      const mom = v.momentum != null ? v.momentum : 0;
      const mood = v.mood || "netral";
      const moodLabel = mood === "bullish" ? "menguntungkan" : (mood === "bearish" ? "memberatkan" : "netral");
      const momLabel = mom >= 0.15 ? "menguat" : (mom <= -0.15 ? "melemah" : "stabil");
      return `
        <button type="button" class="driver-card" data-driver="${esc(v.id)}" title="Klik untuk melihat ${v.articles} berita terkait">
          <div class="driver-name">${esc(v.name)}</div>
          <div class="driver-notes">${esc(v.notes)}</div>
          <div class="driver-meta">
            <span class="pill ${mood}">a:: ${moodLabel}</span>
            <span class="pill hz">momentum: ${momLabel} (${mom.toFixed(2)})</span>
            <span class="chip">${v.articles} berita</span>
          </div>
        </button>`;
    }).join("");
    $("#driversList").innerHTML = `<div class="driver-grid">${cards}</div>`;
  }

  function renderThemes(d) {
    const themes = (d && d.themes) || [];
    const note = $("#themeNote");
    if (note) note.textContent = `(${themes.length} tema)` ;
    if (!themes.length) {
      $("#themesList").innerHTML = `<div class="empty">Belum ada data tema.</div>`;
      return;
    }
    const cards = themes.map(t => {
      const mom = t.momentum != null ? t.momentum : 0;
      const momLabel = mom >= 0.15 ? "menguat" : (mom <= -0.15 ? "melemah" : "stabil");
      const momClass = mom >= 0.15 ? "bullish" : (mom <= -0.15 ? "bearish" : "netral");
      return `
        <button type="button" class="theme-card" data-theme="${esc(t.id)}" title="Klik untuk lihat sektor, saham & berita terkait">
          <div class="theme-name">${esc(t.name)}</div>
          <div class="theme-desc">${esc(t.description)}</div>
          <div class="theme-meta">
            <span class="pill ${momClass}">momentum: ${momLabel} (${mom.toFixed(2)})</span>
            <span class="chip">${t.articles} berita</span>
          </div>
        </button>`;
    }).join("");
    $("#themesList").innerHTML = `<div class="theme-grid">${cards}</div>`;
  }

  function renderPriceWatch(pd) {
    const watch = (pd && pd.watch) || [];
    const model = (pd && pd.model) || {};
    PWATCH = watch;

    // info pembaruan prediksi (dari API /api/prices -> model.last_prediction_update)
    const lu = (model && model.last_prediction_update) || null;
    const infoEl = $("#predUpdateInfo");
    if (infoEl) {
      infoEl.innerHTML = lu
        ? `Prediksi diperbarui: <b>${esc(fmtDateTime(lu))}</b> (SGT)`
        : `Prediksi diperbarui: <b>–</b> (belum ada evaluasi)`;
    }

    const hz = model.horizons || {};
    const chips = ["short", "medium", "long"].map(h => {
      const v = hz[h];
      if (!v) return `<span class="pill hz">${esc(hzLabel(h))}: belum ada data</span>`;
      return `<span class="pill hz">${esc(hzLabel(h))} · akurasi ${Math.round(v.accuracy * 100)}% (${v.correct}/${v.total})</span>`;
    }).join("");
    $("#modelStats").innerHTML = chips;

    if (!watch.length) {
      $("#priceWatchList").innerHTML =
        `<div class="empty">Belum ada saham untuk dipantau.</div>`;
      return;
    }

    const cards = watch.map(w => {
      const series = w.series || [];
      const svg = sparkline(series);
      const last = w.latest_close != null
        ? Number(w.latest_close).toLocaleString("id-ID") : "–";
      let chgHtml = "";
      if (series.length >= 2) {
        const first = Number(series[0].close), lastc = Number(series[series.length - 1].close);
        if (first && lastc) {
          const chg = (lastc - first) / first * 100;
          chgHtml = `<span class="pill ${chg >= 0 ? "bullish" : "bearish"}">${chg >= 0 ? "+" : ""}${chg.toFixed(2)}% (periode)</span>`;
        }
      }
      return `
        <div class="pw-card" data-code="${esc(w.code)}">
          <div class="pw-head">
            <div>
              <div class="rec-code">${esc(w.code)}</div>
              <div class="rec-name">${esc(w.name)}</div>
            </div>
            <div class="pw-rhs">
              <div class="pw-price">${last}</div>
              <div class="pw-date">${esc(fmtDate(w.latest_date))}</div>
            </div>
          </div>
          <div class="rec-meta">${esc(w.sector_name)} · ${esc(hzLabel(w.horizon))}</div>
          <div class="chart-wrap" data-code="${esc(w.code)}">
            ${svg}
            <div class="cu-line"></div>
            <div class="cu-panel"><div class="d"></div><div class="p"></div></div>
          </div>
          <div class="pw-footer">${chgHtml}</div>
        </div>`;
    }).join("");

    $("#priceWatchList").innerHTML = `<div class="pw-grid">${cards}</div>`;
  }

  function renderPerf() {
    const panel = $("#perfPanel");
    const p = MODEL_DATA && MODEL_DATA.performances;
    if (!panel) return;
    if (!p || !p.length) {
      panel.innerHTML = `<div class="empty">Belum ada evaluasi prediksi.</div>`;
      return;
    }
    const rows = p.map(x => {
      const outClass = x.outcome === "menang" ? "bullish"
        : (x.outcome === "kalah" ? "bearish" : "netral");
      return `
        <tr>
          <td>${esc(fmtDate(x.date))}</td>
          <td><b>${esc(x.code)}</b> ${esc(x.name)}</td>
          <td>${esc(x.sector_name || x.sector)}</td>
          <td>${esc(hzLabel(x.horizon))}</td>
          <td>${(x.entry_price != null ? Number(x.entry_price).toLocaleString("id-ID") : "–")}</td>
          <td>${(x.current_price != null ? Number(x.current_price).toLocaleString("id-ID") : "–")}</td>
          <td style="color:var(--muted)">${(x.pct_change != null ? x.pct_change.toFixed(2) + "%" : "–")}</td>
          <td><span class="pill ${outClass}">${esc(x.outcome)}</span></td>
        </tr>`;
    }).join("");
    panel.innerHTML = `
      <div class="perf-head">
        Daftar rekomendasi yang telah dievaluasi — "menang" berarti harga naik sejak direkomendasikan.
      </div>
      <table>
        <thead><tr>
          <th>Tanggal</th><th>Saham</th><th>Sektor</th><th>Horizon</th>
          <th>Harga Masuk</th><th>Harga Kini</th><th>Δ %</th><th>Hasil</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  function renderNews() {
    const news = (newsFilter ? FILTERED_NEWS : ALL_NEWS) || [];
    if (!news.length) {
      const msg = newsFilter
        ? `<div class="empty">Tidak ada berita terkait ${newsFilter.kind === "sector" ? "sektor" : "saham"} <b>${esc(newsFilter.name)}</b>.</div>`
        : `<div class="empty">Belum ada berita.</div>`;
      $("#newsList").innerHTML = msg;
      return;
    }

    const what = newsFilter
      ? (newsFilter.kind === "sector" ? "sektor"
         : (newsFilter.kind === "driver" ? "pendorong pasar" : "saham"))
      : "saham";
    const suffix = (!newsFilter || newsFilter.kind === "sector" || newsFilter.kind === "driver")
      ? "" : ` (${esc(newsFilter.code)})`;
    const banner = newsFilter ? `
      <div class="filter-banner">
        <span>Menampilkan <b>${news.length}</b> berita terkait ${what}
        <b>${esc(newsFilter.name)}</b>${suffix}</span>
        <button class="btn" id="clearFilter">✕ Hapus filter</button>
      </div>` : "";

    const items = news.map(n => {
      let analysis = {};
      try { analysis = JSON.parse(n.analysis_json || "{}"); } catch (e) {}
      const sectors = Object.values(analysis.sectors || {}).slice(0, 3);
      const sectorChips = sectors.map(si =>
        `<span class="chip"><b>Sektor:</b> ${esc(si.name)}</span>`).join("");
      const ticChips = sectors.flatMap(si => si.tickers || []).slice(0, 6).map(t =>
        `<span class="chip tic" data-filter-ticker="${esc(t.code)}" data-filter-name="${esc(t.name)}" title="Klik untuk filter">${esc(t.code)}</span>`).join("");
      const hzChips = (analysis.horizons || []).map(h =>
        `<span class="chip hz">${esc(hzLabel(h))}</span>`).join("");
      const catChip = analysis.category_name
        ? `<span class="chip cat">${esc(analysis.category_name)}</span>` : "";

      const when = n.published ? new Date(n.published).toLocaleString("id-ID") : "";
      const link = n.link && /^https?:\/\//i.test(n.link)
        ? n.link
        : "";
      const linkHtml = link
        ? `<a class="news-link" href="${esc(link)}" target="_blank" rel="noopener">↗ Baca selengkapnya</a>`
        : "";
      return `
        <div class="news-item">
          <div class="top">
            <h3>${esc(n.title)}</h3>
            ${sentimentPill(analysis.label || "netral")}
          </div>
          <div class="meta">${esc(n.source_name) || ""} · ${esc(when)} · ${esc(n.country)}</div>
          ${n.summary ? `<div class="summary">${esc(n.summary)}</div>` : ""}
          <div class="chips">${catChip}${hzChips}${sectorChips}${ticChips}</div>
          ${linkHtml}
        </div>`;
    }).join("");

    $("#newsList").innerHTML = banner + `<div class="news">${items}</div>`;
  }

  function renderHealth(d, dash) {
    const badge = $("#healthBadge");
    const syncTime = $("#syncTime");
    const syncData = $("#syncData");
    if (d && d.status === "ok") {
      const last = d.last_run_day || "—";
      badge.textContent = `sinkron · ${last}`;
      badge.className = "pill bullish";
      if (syncTime) syncTime.textContent = fmtDateTime(d.last_run);
      // "Update data terbaru" = tanggal terbit artikel paling baru
      const news = (dash && dash.recent_news) || [];
      if (syncData) {
        syncData.textContent = news.length ? fmtDateTime(news[0].published) : "–";
      }
    } else {
      badge.textContent = "API tidak tersedia";
      badge.className = "pill bearish";
      if (syncTime) syncTime.textContent = "–";
      if (syncData) syncData.textContent = "–";
    }
  }

  async function loadAll() {
    try {
      // nonce untuk memaksa data segar (hindari cache browser)
      const n = Date.now();
      const [dash, healthRes, priceData, modelData] = await Promise.all([
        fetch(apiUrl("dashboard", { _: n })).then(r => r.json()),
        fetch(apiUrl("health", { _: n })).then(r => r.json()).catch(() => ({ status: "down" })),
        fetch(apiUrl("prices", { _: n })).then(r => r.json()).catch(() => ({ watch: [], model: {} })),
        fetch(apiUrl("model", { _: n })).then(r => r.json()).catch(() => null),
      ]);
      MODEL_DATA = modelData;
      ALL_NEWS = dash.recent_news || [];
      renderHealth(healthRes, dash);
      renderSummary(dash);
      renderRecommendations(dash);
      renderDrivers(dash);
      renderThemes(dash);
      renderPriceWatch(priceData);
      renderMatrix(dash);
      renderNews();
    } catch (e) {
      $("#summaryCards").innerHTML = `<div class="empty">Gagal memuat data: ${esc(e.message)}</div>`;
    }
  }

  async function refreshPriceWatch() {
    try {
      const r = await fetch(apiUrl("prices"));
      renderPriceWatch(await r.json());
    } catch (e) {
      $("#priceWatchList").innerHTML =
        `<div class="empty">Gagal memuat harga: ${esc(e.message)}</div>`;
    }
  }

  // Di GitHub Pages tidak ada server: pembaruan berjalan terjadwal (GitHub Actions)
  if (STATIC) {
    $("#refreshBtn").style.display = "none";
    $("#checkPricesBtn").style.display = "none";
  }

  $("#refreshBtn").addEventListener("click", async () => {
    const btn = $("#refreshBtn");
    btn.disabled = true; btn.textContent = "Memperbarui…";
    try {
      await fetch("/api/refresh", { method: "POST" });
      await loadAll();
    } catch (e) {
      alert("Gagal memperbarui: " + e.message);
    } finally {
      btn.disabled = false; btn.textContent = "↻ Perbarui Sekarang";
    }
  });

  $("#perfBtn").addEventListener("click", () => {
    const panel = $("#perfPanel");
    if (!panel) return;
    if (panel.hidden) { renderPerf(); panel.hidden = false; }
    else panel.hidden = true;
  });

  $("#checkPricesBtn").addEventListener("click", async () => {
    const b = $("#checkPricesBtn");
    b.disabled = true; b.textContent = "Memperbarui prediksi…";
    try {
      await fetch("/api/check", { method: "POST" });
      await refreshPriceWatch();
    } catch (e) {
      alert("Gagal memperbarui prediksi: " + e.message);
    } finally {
      b.disabled = false; b.textContent = "↻ Perbarui Prediksi";
    }
  });

  // --- Modal layar penuh untuk grafik harga ---
  function openPriceModal(w) {
    if (!w) return;
    $("#modalTitle").textContent = `${w.code} — ${w.name}`;
    const series = w.series || [];
    const last = w.latest_close != null
      ? Number(w.latest_close).toLocaleString("id-ID") : "–";
    $("#modalInfo").innerHTML = `
      <span>💰 ${esc(w.sector_name)}</span>
      <span>Horizon: <b>${esc(hzLabel(w.horizon))}</b></span>
      <span>Harga terakhir: <b>${last}</b> · ${esc(fmtDate(w.latest_date))}</span>
      <span>Jumlah hari: <b>${series.length}</b></span>`;
    $("#modalChart").innerHTML = `
      <div class="chart-wrap" data-code="${esc(w.code)}">
        ${sparkline(series, 860)}
        <div class="cu-line"></div>
        <div class="cu-panel"><div class="d"></div><div class="p"></div></div>
      </div>`;
    const m = $("#priceModal");
    if (m) { m.hidden = false; document.body.style.overflow = "hidden"; }
  }

  function closePriceModal() {
    const m = $("#priceModal");
    if (m) m.hidden = true;
    document.body.style.overflow = "";
  }

  // --- Modal detail tema struktural ---
  async function openThemeModal(id) {
    const m = $("#themeModal");
    if (!m) return;
    m.hidden = false;
    document.body.style.overflow = "hidden";
    const title = $("#themeModalTitle");
    const body = $("#themeModalBody");
    title.textContent = "Memuat…";
    body.innerHTML = `<div class="loading">Memuat detail tema…</div>`;
    try {
      const r = await fetch(apiUrl("themes/" + encodeURIComponent(id)));
      const d = await r.json();
      if (d.error) throw new Error(d.error);
      title.textContent = d.name;

      // sektor & saham terkait
      let secHtml = "";
      if (d.sectors && d.sectors.length) {
        secHtml = `<div class="tm-sub">Sektor & saham terkait</div><div class="tm-sectors">` +
          d.sectors.map(s => {
            const st = (s.stocks || []).map(x =>
              `<span class="chip tic" data-filter-ticker="${esc(x.code)}" data-filter-name="${esc(x.name)}">${esc(x.code)}</span>`).join(" ");
            return `<div class="tm-sector"><b>${esc(s.sector_name)}</b><div class="tm-stocks">${st}</div></div>`;
          }).join("") + `</div>`;
      }

      // daftar berita
      const news = (d.news || []).map(n => {
        let an = {};
        try { an = JSON.parse(n.analysis || "{}"); } catch (e) {}
        const link = n.link && /^https?:\/\//i.test(n.link) ? n.link : "";
        return `
          <div class="tm-news">
            <div class="tm-news-top">
              <span class="news-title">${esc(n.title)}</span>
              ${sentimentPill(an.label || "netral")}
            </div>
            <div class="meta">${esc(n.source_name) || ""} · ${esc(fmtDate(n.published))}</div>
            ${link ? `<a class="news-link" href="${esc(link)}" target="_blank" rel="noopener">↗ Baca selengkapnya</a>` : ""}
          </div>`;
      }).join("");

      body.innerHTML = `
        <div class="tm-desc">${esc(d.description)}</div>
        <div class="tm-meta"><span class="chip">${d.articles} berita</span></div>
        ${secHtml}
        <div class="tm-sub">Berita terkait (${d.articles})</div>
        <div class="tm-news-list">${news || '<div class="empty">Belum ada berita terkait.</div>'}</div>`;
    } catch (e) {
      body.innerHTML = `<div class="empty">Gagal memuat: ${esc(e.message)}</div>`;
    }
  }

  function closeThemeModal() {
    const m = $("#themeModal");
    if (m) m.hidden = true;
    document.body.style.overflow = "";
  }

  document.addEventListener("click", (e) => {
    if (e.target.closest("#themeModalClose") || e.target.closest("#themeModalBackdrop")) {
      closeThemeModal();
      return;
    }
    const themeBtn = e.target.closest("[data-theme]");
    if (themeBtn) {
      openThemeModal(themeBtn.getAttribute("data-theme"));
      return;
    }
    if (e.target.closest("#modalClose") || e.target.closest("#priceModalBackdrop")) {
      closePriceModal();
      return;
    }
    const card = e.target.closest(".pw-card");
    if (card) {
      const code = card.getAttribute("data-code");
      const w = PWATCH.find(x => x.code === code);
      if (w) openPriceModal(w);
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closePriceModal();
  });

  // --- Crosshair: garis vertikal dapat digeser + panel harga/tanggal ---
  function updateCrosshair(e) {
    const wrap = e.target.closest && e.target.closest(".chart-wrap");
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    if (!rect.width) return;
    const frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    const code = wrap.getAttribute("data-code");
    const w = PWATCH.find(x => x.code === code);
    if (!w || !w.series || w.series.length < 2) return;
    const n = w.series.length;
    const i = Math.round(frac * (n - 1));
    const ln = wrap.querySelector(".cu-line");
    const pn = wrap.querySelector(".cu-panel");
    if (!ln || !pn) return;
    ln.style.display = "block";
    ln.style.left = (frac * 100) + "%";
    const s = w.series[i];
    if (s) {
      const d = pn.querySelector(".d"), p = pn.querySelector(".p");
      if (d) d.textContent = fmtDate(s.date) || "–";
      if (p) p.textContent = (s.close != null ? Number(s.close).toLocaleString("id-ID") : "–");
    }
    pn.style.display = "block";
    const pct = Math.min(88, Math.max(12, frac * 100));
    pn.style.left = pct + "%";
  }

  function hideCrosshair(e) {
    const wrap = e.target.closest && e.target.closest(".chart-wrap");
    if (!wrap) return;
    const to = e.relatedTarget;
    const inside = to && to.closest && to.closest(".chart-wrap") === wrap;
    if (inside) return;
    const ln = wrap.querySelector(".cu-line"), pn = wrap.querySelector(".cu-panel");
    if (ln) ln.style.display = "none";
    if (pn) pn.style.display = "none";
  }

  document.addEventListener("mousemove", updateCrosshair);
  document.addEventListener("mouseout", hideCrosshair);

  // --- Filter berita berdasarkan saham/ticker, sektor, atau driver ---
  async function applyNewsFilter(kind, code, name) {
    if (!code) return;
    newsFilter = { kind, code, name: name || code };
    if (kind === "ticker") newsFilter.code = code.toUpperCase();
    FILTERED_NEWS = null;
    $("#newsList").innerHTML =
      `<div class="loading">Mencari berita terkait ${esc(newsFilter.name)}…</div>`;
    const param = kind === "sector" ? "sector" : (kind === "driver" ? "driver" : "ticker");
    try {
      const r = await fetch(apiUrl("news", { [param]: newsFilter.code }));
      // mode statis: saham di luar daftar config tidak punya file -> anggap kosong
      const d = (STATIC && r.status === 404) ? { articles: [] } : await r.json();
      FILTERED_NEWS = d.articles || [];
      renderNews();
      const el = document.getElementById("newsList");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      alert("Gagal memuat berita terkait: " + e.message);
      newsFilter = null;
      FILTERED_NEWS = null;
      renderNews();
    }
  }

  document.addEventListener("click", (e) => {
    const tic = e.target.closest("[data-filter-ticker]");
    if (tic) {
      applyNewsFilter("ticker", tic.getAttribute("data-filter-ticker"),
                      tic.getAttribute("data-filter-name"));
      return;
    }
    const sec = e.target.closest("[data-filter-sector]");
    if (sec) {
      applyNewsFilter("sector", sec.getAttribute("data-filter-sector"),
                      sec.getAttribute("data-filter-name"));
      return;
    }
    const drv = e.target.closest("[data-driver]");
    if (drv) {
      applyNewsFilter("driver", drv.getAttribute("data-driver"),
                      drv.querySelector(".driver-name") ? drv.querySelector(".driver-name").textContent : "Driver");
      return;
    }
    if (e.target.closest("#clearFilter")) {
      newsFilter = null;
      FILTERED_NEWS = null;
      renderNews();
    }
  });

  (async () => {
    await loadConfig();
    await loadAll();
  })();

  // Perbarui dashboard secara berkala (60 dtk) agar otomatis
  // merefleksikan pembaruan berita dari backend.
  setInterval(async () => {
    if (document.hidden) return;   // hemat sumber daya saat tab tidak aktif
    await loadAll();
  }, 60000);
})();
