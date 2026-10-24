# Pasar Intel — IHSG 🗞️📈

Website agregator berita otomatis (dalam & luar negeri) yang memproses berita
setiap hari dan memberikan **pertimbangan dampak sektor & saham IHSG**, lengkap
dengan proyeksi arah (bullish/bearish) untuk tiga horizon waktu:

| Horizon | Jangka |
|---|---|
| **Pendek** | 1–3 bulan |
| **Menengah** | 3–12 bulan |
| **Panjang** | 1–10 tahun |

> ⚠️ **Penting:** Alat ini bersifat *informasi/pertimbangan*, **bukan nasihat
> investasi**. Dibangun di atas leksikon sentimen dan aturan heuristik, bukan
> jaminan akurasi. Selalu lakukan riset mandiri dan konsultasikan dengan
> profesional sebelum mengambil keputusan.

---

## Cara menjalankan

**Prasyarat:** Python 3.10+ (belum terpasang di mesin ini — install dari
[python.org](https://www.python.org/downloads/) dan centang *"Add Python to PATH"*).

```bash
cd ihsg-intel
pip install -r requirements.txt
python main.py
```

Lalu buka **http://localhost:8000** di browser.

- Saat aplikasi dinyalakan (komputer online), **berita langsung diambil**
  dalam beberapa detik, lalu **pembaruan otomatis berulang setiap 1 jam**
  selama komputer/aplikasi aktif.
- Tombol **"Perbarui Sekarang"** di dashboard memicu pengambilan + analisis manual.

---

## Cara kerja (alur otomatis)

```
 RSS (dalam & luar negeri)
   │  fetch_news.py (feedparser)
   ▼
 Klasifikasi per artikel (classify.py)
   │  • sentimen leksikon ID/EN (dgn penanganan negasi & penguat)
   │  • deteksi sektor terdampak (kata kunci sektor → ticker)
   │  • deteksi kategori berita → horizon waktu (heuristik)
   ▼
 Simpan ke SQLite (db.py)
   ▼
 Agregasi sinyal sektor harian (analyzer.py)
   │  • net bullish/bearish per horizon (pendek/menengah/panjang)
   │  • daftar ticker terdampak + headline pendukung
   ▼
 Dashboard web (FastAPI + static)
```

### Sumber berita (RSS) — `config.py → SOURCES`
**Dalam negeri:** CNBC Indonesia, CNN Indonesia, Detik Finance, Kompas Money,
Tempo Ekonomi, Bisnis.com, BeritaSatu, **IDX Channel**, **Katadata**,
**Kontan Investasi** (scraper daftar berita).
**Luar negeri:** Reuters, Al Jazeera, Nikkei Asia, The Economist, Financial Times,
**Bloomberg Markets**.

> **Catatan IDX:** Laman resmi Bursa Efek Indonesia (`idx.co.id`) memakai
> proteksi anti-bot (403) sehingga **tidak bisa diambil langsung**. Berita/
> pengumuman terkait IDX tersedia melalui IDX Channel, Katadata, dan Kontan
> yang sudah terpasang.

Tambahkan/ubah sumber hanya di `config.py`.

### Horizon waktu — diatur kategori berita
| Kategori | Horizon |
|---|---|
| Korporasi (laba, akuisisi, kontrak) | Pendek |
| Komoditas (harga emas, nikel, CPO) | Pendek + Menengah |
| Kebijakan moneter / suku bunga | Pendek + Menengah |
| Makroekonomi | Menengah |
| Fiskal / anggaran | Menengah + Panjang |
| Geopolitik / global | Menengah + Panjang |
| Bencana / gangguan | Pendek |

---

## Deploy gratis ke GitHub Pages (otomatis tiap jam)

Tanpa server: GitHub Actions menjalankan `build_static.py` setiap jam, yaitu
mengambil berita, menganalisis, mengevaluasi prediksi sekali sehari (setelah 17:05 SGT),
lalu menerbitkan dashboard sebagai situs statis (data API disimpan sebagai file JSON).

1. Buat repository **Public** di GitHub, lalu unggah seluruh isi folder ini
   (termasuk folder `.github` dan `data/pasar_intel.db` sebagai data awal).
2. Buka **Settings → Pages**, pada **Source** pilih **GitHub Actions**.
3. Buka tab **Actions** → workflow **Perbarui & terbitkan dashboard** →
   **Run workflow** untuk run pertama (berikutnya berjalan otomatis tiap jam).
4. Situs tayang di `https://<username>.github.io/<nama-repo>/`.

Catatan mode GitHub Pages:
- Tombol "Perbarui Sekarang" dan "Perbarui Prediksi" disembunyikan; pembaruan
  manual dilakukan lewat **Actions → Run workflow**.
- Database terbaru disimpan di situs (`state/pasar_intel.db.gz`) dan dipulihkan
  di awal setiap run, sehingga riwayat & bobot "belajar" berlanjut.
- Jadwal GitHub Actions bisa terlambat beberapa menit, dan GitHub menonaktifkan
  jadwal pada repo publik yang tidak ada aktivitas commit selama 60 hari
  (aktifkan lagi dari tab Actions).
- Uji lokal: `python build_static.py --no-fetch`, lalu buka folder `_site/`
  lewat server statis (mis. `python -m http.server -d _site`).

---

## Deploy ke server cloud permanen (VPS)

Aplikasi dapat dijalankan 24/7 di VPS (Ubuntu/Debian) sehingga bisa diakses dari
mana saja. Data tersimpan di SQLite (`data/pasar_intel.db`) — cukup ikut disalin
bersama kode.

**Langkah:**

1. **Salin kode ke VPS** — mis. lewat SCP/Git:
   ```bash
   scp -r ihsg-intel user@IP-VPS:/tmp/ihsg-intel
   ```
2. **Jalankan script installer** di VPS (sebagai root):
   ```bash
   cd /tmp/ihsg-intel/deploy
   chmod +x install_server.sh
   sudo bash install_server.sh
   ```
   Script ini: install Python & dependensi, buat user khusus, pasang **systemd
   service** (auto-start saat reboot), dan menyalakan aplikasi di port 8000.

3. **Buka port 8000** di firewall VPS (ufw / panel penyedia) untuk akses publik.

4. Akses dashboard dari komputer mana pun: `http://<IP-VPS>:8000`

> **Catatan:** service systemd (`pasar-intel.service`) otomatis menjalankan
> scheduler (update tiap jam + evaluasi harian) selama VPS menyala, jadi tidak
> perlu membuka dashboard untuk tetap berjalan. Jika ingin menyalin **database
> yang sudah ada**, upload `data/pasar_intel.db` ke `/opt/pasar-intel/data/`
> sebelum/tetelah install.

---

## Struktur berkas

```
ihsg-intel/
├── main.py              # FastAPI: API + dashboard + lifespan (seed & scheduler)
├── scheduler.py         # penjadwal harian (APScheduler, 06:00/12:00/18:00 SGT)
├── build_static.py      # versi statis untuk GitHub Pages (dipakai GitHub Actions)
├── .github/workflows/pages.yml  # jadwal tiap jam + deploy GitHub Pages
├── config.py            # sektor, saham, sumber RSS, kategori, horizon, ambang
├── requirements.txt
├── core/
│   ├── fetch_news.py    # pengambil & pembersih RSS
│   ├── classify.py      # sentimen + deteksi sektor + kategori/horizon
│   ├── analyzer.py      # orkestrasi + agregasi sinyal sektor harian
│   ├── db.py            # lapisan SQLite (stdlib)
│   ├── lexicon.py       # leksikon sentimen Indonesia & Inggris
│   └── seed.py          # data contoh agar dashboard langsung terisi
├── data/                # db sqlite (dibuat otomatis)
└── static/
    ├── index.html # dashboard
    ├── style.css
    └── app.js
```

---

## API

| Endpoint | Deskripsi |
|---|---|
| `GET /` | Dashboard web |
| `GET /api/health` | Status, jumlah artikel, waktu run terakhir |
| `GET /api/dashboard` | Ringkasan: sinyal sektor + berita terbaru |
| `GET /api/news?limit=&date=` | Berita tersimpan (analisis JSON) |
| `GET /api/signals?date=` | Sinyal sektor per tanggal |
| `GET /api/recommendations?date=` | Rekomendasi saham per horizon |
| `GET /api/model` | Akurasi riwayat + bobot hasil belajar per sektor/horizon |
| `POST /api/check` | Perbarui prediksi: sinkronkan harga + evaluasi akurasi |
| `GET /api/price?code=ACES` | Riwayat harga harian satu saham |
| `GET /api/prices` | Harga + grafik untuk saham-saham rekomendasi |

---

## Belajar dari pengalaman (update prediksi) & pemantauan harga

Aplikasi **belajar dari riwayat**: rekomendasi sebelumnya dipantau harganya
untuk mengukur apakah prediksi "bullish" terbukti, lalu bobot per sektor/horizon
disesuaikan (dinaikkan jika akurat, diturunkan jika tidak). Bobot ini dipakai
lagi untuk analisis berikutnya.

- **Sumber harga:** Yahoo Finance (gratis, tanpa API key), kode IDX memakai
  akhiran `.JK` (contoh `ACES.JK`). Data disimpan di SQLite (`prices`).
- **Evaluasi otomatis:** sekali sehari (default 17:05 SGT, +8 Singapura) harga di-sinkronkan
  dan akurasi diperbarui; bisa juga dipicu manual via tombol **"↻ Perbarui Prediksi"**
  di dashboard atau `POST /api/check`.
- **Grafik harga harian** ditampilkan untuk setiap saham yang masuk rekomendasi
  (bagian "Pemantauan Harga & Belajar Prediksi").
| `GET /api/sectors` | Daftar sektor & saham |
| `GET /api/config` | Horizon, kategori, sumber |
| `POST /api/refresh` | Jalankan siklus pengambilan + analisis manual |

---

## Kustomisasi

- **Sektor & saham** → edit `config.py → SECTORS`.
- **Kata sentimen** → tambahkan ke `core/lexicon.py`.
- **Sumber RSS** → tambahkan di `config.py → SOURCES`.
- **Jadwal harian** → ubah `config.py → SCHEDULE_HOURS`.
- **Mematikan scheduler** → set env `DISABLE_SCHEDULER=1`.

---

## Batasan (jujur)

1. Leksikon sentimen adalah versi prototipe; akurasi perlu dievaluasi dengan data nyata.
2. Aturan horizon bersifat heuristik, bukan model keuangan.
3. RSS bisa gagal/tutup; setiap kegagalan dicatat dan tidak menggagalkan siklus.
4. "Belajar" di sini adalah mekanisme heuristik (menyesuaikan bobot berdasarkan
   akurasi riwayat), bukan pelatihan model ML penuh. Evaluasi awal bisa terjadi
   sebelum horizon berakhir sehingga ukurannya masih perkiraan.
5. Harga bersumber dari Yahoo Finance; jika layanan tersebut berubah/offline,
   grafik & evaluasi tidak bisa diperbarui. Verifikasi ulang data harga sebelum
   dipakai untuk keputusan.
6. Untuk produksi: tambahkan otentikasi, penyimpanan cloud, dan peringatan saat
   RSS/kegagalan harga terjadi terus-menerus.
