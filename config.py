# -*- coding: utf-8 -*-
"""
Konfigurasi pusat aplikasi Pasar Intel — IHSG.
Berisi daftar sektor (IDX-IC), pemetaan saham ke sektor, sumber RSS,
kategori berita, dan bobot horizon waktu.
"""

APP_NAME = "Pasar Intel — IHSG"
APP_DESC = "Agregator berita otomatis untuk mempertimbangkan dampak sektor & saham IHSG"

# ---------------------------------------------------------------------------
# SEKTOR & SAHAM
# ---------------------------------------------------------------------------
# struktur: kode_sektor -> {name, keywords: [..], tickers: [(kode, nama), ...]}
SECTORS = {
    "ENERGY": {
        "name": "Energi",
        "keywords": ["minyak", "oil", "batu bara", "batubara", "coal", "gas",
                     "energi", "energy", "opec", "opec", "crude", "bumi",
                     "geothermal", "panas bumi", "lpg", "bnb", "harga minyak"],
        "tickers": [
            ("ADRO", "Adaro Energy"), ("PTBA", "Bukit Asam"), ("MEDC", "Medco Energi"),
            ("INDY", "Indika Energy"), ("KKGI", "Resource Alam Indonesia"), ("PGAS", "Perusahaan Gas Negara"),
            ("ELSA", "Elnusa"), ("AKRA", "AKR Corporindo"), ("BRMS", "Bumi Resources Minerals"),
            ("ESSA", "Surya Esa Perkasa"), ("ITMG", "Indo Tambangraya Megah"),
            ("HRUM", "Harum Energy"), ("BUMI", "Bumi Resources"), ("TOBA", "TBS Energi Utama"),
        ],
    },
    "BASIC_MATERIALS": {
        "name": "Bahan Baku",
        "keywords": ["emas", "gold", "nikel", "nickel", "tembaga", "copper", "aluminium",
                     "aluminum", "semen", "cement", "kimia", "chemical", "baja", "steel",
                     "tambang", "mining", "timah", "tin", "bauksit", "smelter", "nikel"],
        "tickers": [
            ("ANTM", "Aneka Tambang"), ("INCO", "Vale Indonesia"), ("MDKA", "Merdeka Copper Gold"),
            ("TINS", "Timah"), ("SMGR", "Semen Indonesia"), ("SMBR", "Semen Baturaja"),
            ("INTP", "Indocement Tunggal Prakarsa"), ("BRPT", "Barito Pacific"), ("TPIA", "Chandra Asri"),
            ("ARKA", "Argha Karya Prima"), ("INKP", "Indah Kiat Pulp & Paper"),
            ("TKIM", "Pabrik Kertas Tjiwi Kimia"), ("IKBI", "Sumi Indo Kabel"),
            ("PTSN", "Sat Nusapersada"),
        ],
    },
    "INDUSTRIALS": {
        "name": "Industri",
        "keywords": ["otomotif", "automotive", "mesin", "machinery", "alat berat", "heavy equipment",
                     "manufaktur", "manufacturing", "baja", "steel", "kereta", "railway",
                     "pesawat", "aviation", "pertahanan", "infrastruktur industri"],
        "tickers": [
            ("ASII", "Astra International"), ("UNTR", "United Tractors"), ("KBLM", "Kabelindo Murni"),
            ("KMTR", "Kirana Megatara"), ("GJTL", "Gajah Tunggal"), ("AUTO", "Astra Otoparts"),
            ("SMSM", "Selamat Sempurna"), ("KJEN", "Kedaung Indah Can"), ("WSKT", "Waskita Karya"),
            ("TOTL", "Total Bangun Persada"), ("GEMA", "Gema Grahasarana"), ("SCCO", "Surya Citra? no"),
        ],
    },
    "FINANCIALS": {
        "name": "Keuangan",
        "keywords": ["bank", "banking", "perbankan", "kredit", "loan", "asuransi", "insurance",
                     "fintech", "multifinance", "pinjaman", "deposito", "suku bunga", "bi rate",
                     "bi7drr", "gjka", "likuiditas", "modal", "kreditur", "lps"],
        "tickers": [
            ("BBCA", "Bank Central Asia"), ("BBRI", "Bank Rakyat Indonesia"), ("BMRI", "Bank Mandiri"),
            ("BBNI", "Bank Negara Indonesia"), ("BTPN", "Bank BTPN"), ("BNGA", "Bank CIMB Niaga"),
            ("BRIS", "Bank Syariah Indonesia"), ("BDMN", "Bank Danamon"), ("PNBN", "Bank Pan Indonesia"),
            ("MEGA", "Bank Mega"), ("ARTO", "Bank Jago"), ("BBHI", "Allo Bank"),
            ("ASMI", "Asuransi Mitra Maparya"), ("AMAG", "Asuransi Multi Artha Guna"),
            ("PNIN", "Panin Financial"), ("AHAP", "Asuransi Harta Aman Pratama"),
            ("ADMF", "Adira Dinamika Multi Finance"), ("BFIN", "Bussan Auto Finance"),
        ],
    },
    "HEALTHCARE": {
        "name": "Kesehatan",
        "keywords": ["farmasi", "pharmacy", "obat", "drug", "rumah sakit", "hospital", "klinik",
                     "vaksin", "vaccine", "kesehatan", "health", "medis", "medical",
                     "laboratorium", "laboratory", "apotek"],
        "tickers": [
            ("KLBF", "Kalbe Farma"), ("KAEF", "Kimia Farma"), ("SIDO", "Sido Muncul"),
            ("MIKA", "Mitra Keluarga Karyasehat"), ("HEAL", "Medikaloka Hermina"),
            ("PRDA", "Prodia Widyahusada"), ("DVLA", "Darya-Varia Laboratoria"),
            ("TSPC", "Tempo Scan Pacific"), ("PYFA", "Pyridam Farma"), ("INAF", "Indofarma"),
            ("MERK", "Merck Indonesia"), ("SCPI", "Organon Pharma Indonesia"),
        ],
    },
    "CONSUMER_NONCYCLICALS": {
        "name": "Barang Konsumen Primer",
        "keywords": ["makanan", "food", "minuman", "beverage", "rokok", "cigarette", "retail",
                     "ritel", "minimarket", "supermarket", "consumer goods", "barang konsumsi",
                     "fmcg", "mi instan", "susu", "milk", "teh", "coffee", "kopi", "pangan",
                     "gula", "sugar", "cpo", "minyak goreng", "pangan"],
        "tickers": [
            ("UNVR", "Unilever Indonesia"), ("ICBP", "Indofood CBP Sukses Makmur"),
            ("INDF", "Indofood Sukses Makmur"), ("MYOR", "Mayora Indah"), ("CPIN", "Charoen Pokphand"),
            ("JPFA", "Japfa Comfeed"), ("TBLA", "Tunas Baru Lampung"), ("AISA", "Tiga Pilar Sejahtera"),
            ("GGRM", "Gudang Garam"), ("HMSP", "HM Sampoerna"), ("WIIM", "Wismilak Inti Makmur"),
            ("MLBI", "Multi Bintang Indonesia"), ("DLTA", "Delta Djakarta"), ("BUDI", "Budi Starch & Sweetener"),
            ("SKLT", "Sekar Laut"), ("CAMP", "Campina Ice Cream"), ("ULTJ", "Ultrajaya Milk Industry"),
            ("ANJT", "Austindo Nusantara Jaya"),
        ],
    },
    "CONSUMER_CYCLICALS": {
        "name": "Barang Konsumen Non-Primer",
        "keywords": ["ritel", "retail", "mall", "pusat perbelanjaan", "elektronik", "electronics",
                     "gadget", "smartphone", "fashion", "garmen", "pariwisata", "tourism",
                     "hotel", "restoran", "restaurant", "hiburan", "entertainment", "media",
                     "otoparts", "kendaraan", "konsumen", "trip", "liburan"],
        "tickers": [
            ("MAPI", "Mitra Adiperkasa"), ("ERAA", "Erajaya Swasembada"), ("ACES", "Ace Hardware Indonesia"),
            ("RALS", "Ramayana Lestari Sentosa"), ("LPPF", "Matahari Department Store"),
            ("MAPA", "Map Aktif Adiperkasa"), ("AMRT", "Sumber Alfaria Trijaya"),
            ("DNET", "Indoritel Makmur Internasional"), ("RANC", "Supra Boga Lestari"),
            ("PANR", "Panorama Sentrawisata"), ("HWSA", "Wijaya Karya Bangunan Gedung"),
            ("JARR", "Jaya Real Property? no"),
        ],
    },
    "PROPERTY": {
        "name": "Properti & Real Estat",
        "keywords": ["properti", "property", "real estate", "perumahan", "apartemen", "apartment",
                     "kawasan industri", "industrial estate", "tanah", "land", "developer",
                     "hunian", "residential", "komersial", "commercial", "konstruksi properti"],
        "tickers": [
            ("CTRA", "Ciputra Development"), ("BSDE", "Bumi Serpong Damai"), ("SMRA", "Summarecon Agung"),
            ("PWON", "Pakuwon Jati"), ("BEST", "Bekasi Fajar Industrial Estate"),
            ("DMAS", "Puradelta Lestari"), ("DUTI", "Duta Pertiwi"), ("MKPI", "Metropolitan Kentjana"),
            ("JRPT", "Jaya Real Property"), ("MTLA", "Metropolitan Land"), ("ASRI", "Alam Sutera Realty"),
            ("LPKR", "Lippo Karawaci"), ("KIJA", "Kawasan Industri Jababeka"), ("PPRO", "PP Properti"),
        ],
    },
    "INFRASTRUCTURE": {
        "name": "Infrastruktur",
        "keywords": ["jalan tol", "toll", "toll road", "pelabuhan", "port", "bandara", "airport",
                     "kereta cepat", "transportasi umum", "telekomunikasi", "telecommunications",
                     "tower", "menara", "listrik", "electricity", "pln", "air bersih", "water",
                     "pipa gas", "jaringan", "broadband", "fibre", "data center", "tol"],
        "tickers": [
            ("WIKA", "Wijaya Karya"), ("JSMR", "Jasa Marga"), ("CMNP", "Citra Marga Nusaphala"),
            ("TLKM", "Telkom Indonesia"), ("EXCL", "XL Axiata"), ("ISAT", "Indosat Ooredoo Hutchison"),
            ("TBIG", "Tower Bersama Infrastructure"), ("TOWR", "Sarana Menara Nusantara"),
            ("BALI", "Bali Towerindo Sentra"), ("IPCM", "Jasa Armada Indonesia"),
            ("CASA", "Capital Financial Indonesia"), ("DCII", "DCI Indonesia"), ("WIFI", "Solusi Sinergi Digital"),
            ("PGEO", "Sumber Daya Energi? no"),
        ],
    },
    "TECHNOLOGY": {
        "name": "Teknologi",
        "keywords": ["teknologi", "technology", "software", "aplikasi", "app", "e-commerce",
                     "internet", "digital", "startup", "artificial intelligence", "ai",
                     "cloud", "data center", "semikonduktor", "semiconductor", "platform",
                     "metaverse", "ml", "big data"],
        "tickers": [
            ("GOTO", "GoTo Gojek Tokopedia"), ("EMTK", "Elang Mahkota Teknologi"),
            ("BUKA", "Bukalapak"), ("MTDL", "Metrodata Electronics"), ("MLPT", "Multipolar Technology"),
            ("ASIM", "Asuransi Jasa Indonesia? no"), ("HDIT", "Hensel Davest Indonesia"),
            ("EDGE", "Steadfast? no"), ("WGS", "Wira Global Solusi"), ("DGNS", "Diagnos Laboratorium Utama"),
        ],
    },
    "TRANSPORTATION": {
        "name": "Transportasi & Logistik",
        "keywords": ["transportasi", "transportation", "logistik", "logistics", "pengiriman",
                     "shipping", "pelayaran", "airline", "maskapai", "kurir", "freight",
                     "angkutan", "kapal", "ship", "kargo", "cargo", "truk"],
        "tickers": [
            ("ASSA", "Adi Sarana Armada"), ("BIRD", "Blue Bird"), ("SAFE", "Steady Safe"),
            ("TMAS", "Temas"), ("SMDR", "Samudera Indonesia"), ("WEHA", "Weha Transportasi Indonesia"),
            ("HELI", "Jasa Armada? no"), ("GIAA", "Garuda Indonesia"), ("KONI", "Perdana Gapuraprima"),
            ("ELPI", "Pelayaran Nasional Bina Buana Raya"), ("HIT", "? no"),
        ],
    },
}

# gabungkan semua ticker ke lookup global
STOCKS = {}
for _sector_key, _sec in SECTORS.items():
    for _code, _name in _sec["tickers"]:
        STOCKS.setdefault(_code, {"name": _name, "sector": _sector_key})

# ---------------------------------------------------------------------------
# CATEGORI BERITA -> pewaktuan dampak
# ---------------------------------------------------------------------------
HORIZONS = {
    "short": {"label": "Pendek", "range": "1–3 bulan"},
    "medium": {"label": "Menengah", "range": "3–12 bulan"},
    "long": {"label": "Panjang", "range": "1–10 tahun"},
}

# setiap kategori: keywords, horizon yang relevan, bobot pengaruh sektor (0-1)
CATEGORIES = {
    "monetary": {
        "name": "Kebijakan Moneter / Suku Bunga",
        "keywords": ["suku bunga", "bi rate", "bi7drr", "the fed", "federal reserve", "inflasi",
                     "inflation", "rate hike", "rate cut", "quantitative", "tapering",
                     "bank indonesia", "gubernur bi", "suku bunga naik", "suku bunga turun",
                     "aro", "rrtbi", "fdi"],
        "horizons": ["short", "medium"],
        "sector_weight": 0.8,
    },
    "fiscal": {
        "name": "Kebijakan Fiskal / Anggaran",
        "keywords": ["apbn", "anggaran", "pajak", "tax", "insentif", "stimulus", "belanja negara",
                     "pemerintah", "government", "subsidi", "subsidy", "fiscal", "defisit apbn",
                     "tax incentive", "tax holiday", "vpn", "lpsk", "penjaminan"],
        "horizons": ["medium", "long"],
        "sector_weight": 0.6,
    },
    "macro": {
        "name": "Ekonomi Makro",
        "keywords": ["pertumbuhan ekonomi", "gdp", "pmi", "tenaga kerja", "pengangguran",
                     "employment", "kurs", "rupiah", "dolar", "exchange rate", "rmb", "yuan",
                     "neraca perdagangan", "trade balance", "cadangan devisa", "foreign exchange",
                     "ekspor", "impor", "export", "import", "daya beli", "purchasing power"],
        "horizons": ["medium"],
        "sector_weight": 0.5,
    },
    "corporate": {
        "name": "Korporasi / Perusahaan",
        "keywords": ["laba", "profit", "pendapatan", "revenue", "dividen", "dividend", "right issue",
                     "akuisisi", "acquisition", "merger", "share buyback", "laporan keuangan",
                     "earnings", "net income", "prospek", "guidance", "capex", "belanja modal",
                     "kontrak", "contract", "winning bid", "tender"],
        "horizons": ["short"],
        "sector_weight": 1.0,
    },
    "commodity": {
        "name": "Harga Komoditas",
        "keywords": ["harga minyak", "oil price", "emas", "gold", "nikel", "nickel",
                     "batu bara", "coal", "cpo", "harga komoditas", "commodity", "crude",
                     "tembaga", "copper", "timah", "tin", "perak", "silver", "pangan",
                     "gandum", "wheat", "karet", "rubber"],
        "horizons": ["short", "medium"],
        "sector_weight": 0.9,
    },
    "geopolitical": {
        "name": "Geopolitik / Global",
        "keywords": ["perang", "war", "sanksi", "sanctions", "embargo", "trade war", "perang dagang",
                     "pemilu", "election", "konflik", "conflict", "coup", "geopolitik",
                     "tarif", "tariff", "perang tarif", "china", "taiwan", "russia", "ukraina",
                     "timur tengah", "middle east", "iran", "israel"],
        "horizons": ["medium", "long"],
        "sector_weight": 0.7,
    },
    "disaster": {
        "name": "Bencana / Gangguan",
        "keywords": ["bencana", "banjir", "flood", "gempa", "earthquake", "tsunami", "kebakaran",
                     "fire", "protes", "protest", "mogok", "strike", "pemadaman", "blackout",
                     "force majeure", "cuaca ekstrem", "extreme weather"],
        "horizons": ["short"],
        "sector_weight": 0.5,
    },
}

# ---------------------------------------------------------------------------
# SUMBER BERITA (RSS)
# ---------------------------------------------------------------------------
SOURCES = [
    # Dalam negeri
    {"id": "cnbc-id", "name": "CNBC Indonesia", "country": "ID", "url": "https://www.cnbcindonesia.com/rss", "lag": "id"},
    {"id": "cnn-id", "name": "CNN Indonesia", "country": "ID", "url": "https://www.cnnindonesia.com/rss", "lag": "id"},
    {"id": "detik-fin", "name": "Detik Finance", "country": "ID", "url": "https://rss.detik.com/finance", "lag": "id"},
    {"id": "kompas-money", "name": "Kompas Money", "country": "ID", "url": "https://money.kompas.com/rss", "lag": "id"},
    {"id": "tempo-eko", "name": "Tempo Ekonomi", "country": "ID", "url": "https://www.tempo.co/rss/ekonomi", "lag": "id"},
    {"id": "bisnis", "name": "Bisnis.com", "country": "ID", "url": "https://finansial.bisnis.com/rss", "lag": "id"},
    {"id": "beritasatu", "name": "BeritaSatu Ekonomi", "country": "ID", "url": "https://rss.beritasatu.com/Ekonomi.xml", "lag": "id"},
    {"id": "idx-channel", "name": "IDX Channel", "country": "ID", "url": "https://www.idxchannel.com/rss", "lag": "id"},
    {"id": "katadata", "name": "Katadata", "country": "ID", "url": "https://katadata.co.id/rss", "lag": "id"},
    {"id": "kontan", "name": "Kontan Investasi", "country": "ID", "url": "https://investasi.kontan.co.id/", "lag": "id", "type": "html_list"},
    # Luar negeri
    {"id": "reuters", "name": "Reuters Business", "country": "INT", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best", "lag": "en"},
    {"id": "aljazeera", "name": "Al Jazeera Business", "country": "INT", "url": "https://www.aljazeera.com/xml/rss/all.xml", "lag": "en"},
    {"id": "nikkei", "name": "Nikkei Asia", "country": "INT", "url": "https://asia.nikkei.com/feed", "lag": "en"},
    {"id": "economist", "name": "The Economist", "country": "INT", "url": "https://www.economist.com/finance-and-economics/rss.xml", "lag": "en"},
    {"id": "ft", "name": "Financial Times", "country": "INT", "url": "https://www.ft.com/rss/home", "lag": "en"},
    {"id": "bloomberg", "name": "Bloomberg Markets", "country": "INT", "url": "https://www.bloomberg.com/feeds/markets/news.rss", "lag": "en"},
]

# ---------------------------------------------------------------------------
# PENGATURAN
# ---------------------------------------------------------------------------
DB_PATH = "data/pasar_intel.db"
TIMEZONE = "Asia/Singapore"
# jadwal harian otomatis (SGT, +8 Singapura)
# Siklus pembaruan otomatis: interval (jam) saat komputer aktif.
UPDATE_INTERVAL_HOURS = 1
# Jeda (detik) setelah server menyala sebelum pembaruan pertama dijalankan.
FIRST_UPDATE_DELAY_SECONDS = 5
SENTIMENT_THRESHOLD = 0.12   # ambang bullish/bearish
MAX_ARTICLES_PER_SOURCE = 30
TOP_RECOMMENDATIONS = 6      # jumlah saham rekomendasi per horizon
# Ambang skor minimal agar sebuah saham masuk rekomendasi (0–?).
# Skor = jumlah sentimen positif × bobot sektor. Semakin besar, makin selektif.
RECOMMENDATION_MIN_SCORE = 0.4

# ---------------------------------------------------------------------------
# PENDORONG PASAR (MARKET DRIVERS) — pendek/menengah
# ---------------------------------------------------------------------------
# Faktor makro yang memengaruhi pergerakan saham. Setiap driver punya:
#   - keywords  : untuk mencocokkan berita
#   - bullish   : daftar (terktor, ticker[], bobot) yang DIUNTUNGKAN jika
#                 sentimen berita driver positif (mis. harga emas naik)
#   - bearish   : daftar sektor/saham yang diuntungkan jika sentimen negatif
#                 (seperti "risk-off" saat perang)
# `direction` menentukan apakah momentum positif dianggap bullish (1) atau
# bearish (-1) terhadap sektor yang diuntungkan.
MARKET_DRIVERS = [
    {
        "id": "interest_rate",
        "name": "Suku Bunga & Kebijakan Moneter",
        "keywords": ["suku bunga", "bi rate", "bi7drr", "the fed", "federal reserve",
                     "the fed", "rate hike", "rate cut", "suku bunga naik",
                     "suku bunga turun", "gubernur bi", "fomc", "ecb", "boj",
                     "yield", "obligasi", "bi rate"],
        "notes": "Penurunan suku bunga umumnya meringankan biaya utang & "
                 "mendorong konsumsi/properti; kenaikan suku bunga menekan "
                 "sektor properti & utang tinggi namun bisa menambah marjin bank.",
        "direction": 1,
        "bullish": [
            {"sector": "FINANCIALS", "weight": 0.7},
            {"sector": "PROPERTY", "weight": 0.8},
            {"sector": "CONSUMER_CYCLICALS", "weight": 0.6},
        ],
        "bearish": [
            {"sector": "FINANCIALS", "weight": 0.5},
        ],
    },
    {
        "id": "gold",
        "name": "Harga Emas",
        "keywords": ["emas", "gold", "harga emas", "antm", "emas batangan",
                     "logam mulia", "precious metal", "gold price", "bullion"],
        "notes": "Kenaikan harga emas menguntungkan emiten tambang emas.",
        "direction": 1,
        "bullish": [
            {"sector": "BASIC_MATERIALS", "tickers": ["ANTM", "MDKA"], "weight": 1.0},
        ],
        "bearish": [],
    },
    {
        "id": "commodities",
        "name": "Harga Komoditas",
        "keywords": ["komoditas", "commodity", "nikel", "nickel", "batu bara",
                     "coal", "tembaga", "copper", "timah", "tin", "cpo",
                     "minyak sawit", "baja", "harga komoditas", "crude"],
        "notes": "Kenaikan harga komoditas menguntungkan emiten tambang/agrikultur.",
        "direction": 1,
        "bullish": [
            {"sector": "ENERGY", "weight": 0.8},
            {"sector": "BASIC_MATERIALS", "weight": 0.9},
            {"sector": "CONSUMER_NONCYCLICALS", "weight": 0.5},
        ],
        "bearish": [],
    },
    {
        "id": "war_geopolitics",
        "name": "Geopolitik & Perang",
        "keywords": ["perang", "war", "konflik", "conflict", "sanksi", "sanctions",
                     "embargo", "geopolitik", "timur tengah", "middle east",
                     "iran", "israel", "russia", "ukraina", "taiwan", "china",
                     "militer", "military", "defense", "pertahanan"],
        "notes": "Ketegangan geopolitik umumnya menaikkan harga minyak & emas, "
                 "dan menguntungkan sektor pertahanan/energi, sementara "
                 "menekan pasar berisiko.",
        "direction": 1,
        "bullish": [
            {"sector": "ENERGY", "weight": 0.9},
            {"sector": "BASIC_MATERIALS", "tickers": ["ANTM", "MDKA"], "weight": 0.8},
            {"sector": "INDUSTRIALS", "weight": 0.5},
        ],
        "bearish": [],
    },
    {
        "id": "bitcoin",
        "name": "Bitcoin & Aset Kripto",
        "keywords": ["bitcoin", "btc", "kripto", "cryptocurrency", "crypto",
                     "ether", "ethereum", "altcoin", "stablecoin", "blockchain",
                     "kripto"],
        "notes": "Kenaikan Bitcoin mencerminkan selera risiko; menguntungkan "
                 "emiten yang terkait ekosistem digital/fintech/teknologi.",
        "direction": 1,
        "bullish": [
            {"sector": "TECHNOLOGY", "weight": 0.7},
            {"sector": "FINANCIALS", "weight": 0.4},
        ],
        "bearish": [],
    },
]

# ---------------------------------------------------------------------------
# TEMA STRUKTURAL JANGKA PANJANG (1–10 tahun)
# ---------------------------------------------------------------------------
# Setiap tema menggambarkan pergeseran struktural/transformatif yang berlangsung
# bertahun-tahun. `signals` memetakan arah dampak ke sektor IDX:
#   direction=+1 -> sektor diuntungkan (bullish jangka panjang)
#   direction=-1 -> sektor tertekan (tidak dimasukkan rekomendasi beli)
# `base_conviction` = keyakinan dasar tren (0–~2), lalu disesuaikan dengan
# momentum berita terkini.
STRUCTURAL_THEMES = [
    {
        "id": "ev_transition",
        "name": "Transisi Energi: Kendaraan Listrik (BBM → Listrik)",
        "description": "Peralihan dari bahan bakar minyak ke kendaraan listrik: "
                       "mendorong permintaan nikel/baterai, infrastruktur listrik "
                       "& pengisian daya, serta perlahan menekan sektor minyak.",
        "keywords": ["kendaraan listrik", "mobil listrik", "motor listrik", "ev",
                     "baterai", "battery", "charging", "spbu listrik", "bbm",
                     "subsidi bbm", "konversi motor", "generator", "listrik",
                     "energi terbarukan", "cpo", "biodiesel", "green energy"],
        "signals": [
            {"sector": "BASIC_MATERIALS", "direction": 1, "weight": 1.0},  # nikel, baterai
            {"sector": "INFRASTRUCTURE", "direction": 1, "weight": 0.8},    # listrik/charging
            {"sector": "INDUSTRIALS", "direction": 1, "weight": 0.7},       # manufaktur kendaraan
            {"sector": "ENERGY", "direction": -1, "weight": 0.5},           # minyak tergeser
        ],
        "base_conviction": 1.25,
    },
    {
        "id": "renewable_grid",
        "name": "Energi Terbarukan & Jaringan Listrik",
        "description": "Pembangunan pembangkit terbarukan (PLTS/PLTA), jaringan "
                       "transmisi, dan elektrifikasi nasional sebagai penopang "
                       "pertumbuhan infrastruktur jangka panjang.",
        "keywords": ["energi terbarukan", "plts", "plta", "surya", "solar",
                     "geothermal", "panas bumi", "transmisi listrik", "grid",
                     "elektrifikasi", "ruu energi", "net zero", "dekarbonisasi"],
        "signals": [
            {"sector": "INFRASTRUCTURE", "direction": 1, "weight": 1.0},
            {"sector": "ENERGY", "direction": 1, "weight": 0.8},
            {"sector": "BASIC_MATERIALS", "direction": 1, "weight": 0.5},
        ],
        "base_conviction": 1.15,
    },
    {
        "id": "digital_ai",
        "name": "Digitalisasi & Kecerdasan Buatan",
        "description": "Akselerasi adopsi AI, komputasi awan, dan data center "
                       "sebagai pendorong pertumbuhan sektor teknologi & "
                       "telekomunikasi jangka panjang.",
        "keywords": ["kecerdasan buatan", "artificial intelligence", " ai ", "cloud",
                     "data center", "digital", "digitalisasi", "komputasi awan",
                     "broadband", "jaringan 5g", "teknologi"],
        "signals": [
            {"sector": "TECHNOLOGY", "direction": 1, "weight": 1.0},
            {"sector": "INFRASTRUCTURE", "direction": 1, "weight": 0.8},
        ],
        "base_conviction": 1.2,
    },
    {
        "id": "demographics_consumption",
        "name": "Demografi & Konsumsi Rumah Tangga",
        "description": "Banyaknya penduduk muda, kelas menengah yang tumbuh, dan "
                       "urbanisasi mendukung konsumsi jangka panjang serta "
                       "layanan keuangan/sektor properti.",
        "keywords": ["kelas menengah", "urbanisasi", "konsumsi rumah tangga",
                     "daya beli", "demografi", "penduduk", "rintik", "e-commerce",
                     "kredit konsumen", "perumahan"],
        "signals": [
            {"sector": "CONSUMER_NONCYCLICALS", "direction": 1, "weight": 0.9},
            {"sector": "CONSUMER_CYCLICALS", "direction": 1, "weight": 0.8},
            {"sector": "FINANCIALS", "direction": 1, "weight": 0.7},
            {"sector": "PROPERTY", "direction": 1, "weight": 0.6},
        ],
        "base_conviction": 1.0,
    },
    {
        "id": "national_infra",
        "name": "Pembangunan Infrastruktur Nasional",
        "description": "Proyek jalan tol, pelabuhan, kereta, dan pembangunan "
                       "ibu kota baru sebagai pendorong industri konstruksi & "
                       "infrastruktur jangka panjang.",
        "keywords": ["infrastruktur", "jalan tol", "pelabuhan", "bandara",
                     "kereta cepat", "ibu kota baru", "ikn", "konstruksi",
                     "proyek strategis nasional", "belanja infrastruktur"],
        "signals": [
            {"sector": "INFRASTRUCTURE", "direction": 1, "weight": 1.0},
            {"sector": "INDUSTRIALS", "direction": 1, "weight": 0.8},
            {"sector": "PROPERTY", "direction": 1, "weight": 0.6},
        ],
        "base_conviction": 1.1,
    },
    {
        "id": "health_future",
        "name": "Kesehatan & Penuaan Populasi",
        "description": "Kebutuhan layanan kesehatan meningkat seiring penuaan "
                       "populasi, perubahan gaya hidup, dan kesadaran kesehatan: "
                       "rumah sakit, farmasi, vaksin, dan riset bioteknologi "
                       "memiliki permintaan jangka panjang.",
        "keywords": ["kesehatan", "penuaan", "lansia", "rumah sakit", "hospital",
                     "farmasi", "obat", "vaksin", "vaccine", "bioteknologi",
                     "biotech", "riset medis", "laboratorium", "apotek",
                     "asuransi kesehatan", "bpjs", "klinik", "medis"],
        "signals": [
            {"sector": "HEALTHCARE", "direction": 1, "weight": 1.0},
            {"sector": "CONSUMER_NONCYCLICALS", "direction": 1, "weight": 0.4},
        ],
        "base_conviction": 1.15,
    },
    {
        "id": "climate_change",
        "name": "Pemanasan Global & Perubahan Iklim",
        "description": "Adaptasi & mitigasi perubahan iklim: energi bersih, "
                       "retrofitting infrastruktur, ketahanan pangan/air, dan "
                       "material ramah lingkungan menjadi prioritas jangka panjang.",
        "keywords": ["pemanasan global", "perubahan iklim", "climate change",
                     "gas rumah kaca", "karbon", "carbon", "net zero",
                     "dekarbonisasi", "energi bersih", "cuaca ekstrem",
                     "bencana iklim", "banjir", "kekeringan", "ketahanan pangan",
                     "ketahanan air", "lingkungan", "hijau", "sustainable",
                     "esg"],
        "signals": [
            {"sector": "ENERGY", "direction": 1, "weight": 1.0},      # energi bersih
            {"sector": "INFRASTRUCTURE", "direction": 1, "weight": 0.7},
            {"sector": "BASIC_MATERIALS", "direction": 1, "weight": 0.5},
            {"sector": "CONSUMER_NONCYCLICALS", "direction": 1, "weight": 0.4},
        ],
        "base_conviction": 1.1,
    },
    {
        "id": "ai_transformational",
        "name": "Kecerdasan Buatan & Otomatisasi",
        "description": "Penerapan AI di lintas industri (manufaktur, jasa "
                       "keuangan, kesehatan) mendorong produktivitas dan "
                       "permintaan komputasi, chip, serta data center.",
        "keywords": ["kecerdasan buatan", "artificial intelligence", " ai ",
                     "machine learning", "otomatisasi", "automation", "robot",
                     "data center", "komputasi awan", "cloud", "chip",
                     "semikonduktor", "automated", "algoritma"],
        "signals": [
            {"sector": "TECHNOLOGY", "direction": 1, "weight": 1.0},
            {"sector": "INFRASTRUCTURE", "direction": 1, "weight": 0.7},
            {"sector": "INDUSTRIALS", "direction": 1, "weight": 0.5},
            {"sector": "FINANCIALS", "direction": 1, "weight": 0.3},  # fintech/adopsi AI
        ],
        "base_conviction": 1.2,
    },
    {
        "id": "elnino_weather",
        "name": "El Niño & Gangguan Iklim",
        "description": "El Niño menyebabkan kekeringan berkepanjangan yang "
                       "mengganggu produksi pertanian & perkebunan (kelapa "
                       "sawit, pangan), berpotensi menaikkan harga komoditas "
                       "dan menguntungkan emiten yang diuntungkan kenaikan "
                       "harga produk, sementara membebani yang sangat bergantung "
                       "pada hasil panen.",
        "keywords": ["el nino", "elnino", "kekeringan", "drought", "cuaca ekstrem",
                     "kemarau", "gagal panen", "harga pangan", "kelapa sawit",
                     "cpo", "presipitasi", "musim kering", "banjir", "iklim"],
        "signals": [
            {"sector": "CONSUMER_NONCYCLICALS", "direction": 1, "weight": 0.8,
             "tickers": ["TBLA", "ANJT", "CPIN", "JPFA", "BUDI", "SKLT", "ULTJ"]},
            {"sector": "BASIC_MATERIALS", "direction": 1, "weight": 0.4},
        ],
        "base_conviction": 1.1,
    },
    {
        "id": "food_crisis",
        "name": "Ancaman Krisis Pangan",
        "description": "Tekanan pada rantai pasok pangan global (perang, "
                       "iklim, gangguan logistik) mendorong kenaikan harga "
                       "pangan. Menguntungkan produsen & distributor pangan "
                       "yang bisa meneruskan kenaikan harga, serta sektor "
                       "pangan berdaya tahan.",
        "keywords": ["krisis pangan", "food crisis", "harga pangan", "food price",
                     "kelangkaan pangan", "kelaparan", "ketahanan pangan",
                     "gandum", "wheat", "beras", "rice", "gula", "sugar",
                     "impor pangan", "panen", "pangan", "inflasi pangan"],
        "signals": [
            {"sector": "CONSUMER_NONCYCLICALS", "direction": 1, "weight": 0.9,
             "tickers": ["ICBP", "INDF", "MYOR", "CPIN", "JPFA", "ULTJ", "BUDI", "SKLT"]},
        ],
        "base_conviction": 1.15,
    },
    {
        "id": "fuel_crisis",
        "name": "Krisis BBM & Harga Energi",
        "description": "Pergolakan harga BBM (pemangkasan subsidi, kenaikan "
                       "harga minyak) meningkatkan pendapatan segmen hulu "
                       "migas, namun membebani sektor transportasi dan logistik "
                       "yang sangat bergantung bahan bakar.",
        "keywords": ["bbm", "bahan bakar minyak", "subsidi bbm", "harga bbm",
                     "pertalite", "pertamax", "solar", "avtur", "badan pengatur",
                     "gas elpiji", "elpiji", "minyak mentah", "harga minyak",
                     "spot fuel", "bensin", "diesel", "refinery", "kilang",
                     "impor minyak", "pemangkasan subsidi"],
        "signals": [
            {"sector": "ENERGY", "direction": 1, "weight": 0.9,
             "tickers": ["MEDC", "PGAS", "AKRA", "ELSA", "ADRO", "PTBA", "ITMG", "HRUM", "BUMI", "ESSA", "KKGI", "BRMS", "TOBA"]},
            {"sector": "TRANSPORTATION", "direction": -1, "weight": 0.7},
        ],
        "base_conviction": 1.15,
    },
]

# ------------------ PEMANTAUAN HARGA & BELAJAR ------------------
# Panjang riwayat harga (hari) yang diambil per saham.
PRICE_HISTORY_DAYS = 200
# Jumlah contoh minimal per sektor/horizon sebelum bobot "belajar" dipakai.
MODEL_MIN_SAMPLES = 3
# Jam (SGT, +8 Singapura) penjadwalan sinkronisasi harga + evaluasi prediksi.
PRICE_CHECK_HOUR = 17
PRICE_CHECK_MINUTE = 5
# Batas jumlah saham yang dipantau harganya untuk grafik.
PRICE_WATCH_LIMIT = 12
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PasarIntel/1.0"
REQUEST_TIMEOUT = 15
