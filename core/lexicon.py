# -*- coding: utf-8 -*-
"""
Leksikon sentimen dwibahasa (Indonesia & Inggris).
Kata positif bernilai +1, negatif bernilai -1. Digunakan oleh mesin sentimen.

CATATAN: Leksikon ini adalah versi prototipe — bisa diperluas. Sebaiknya
dievaluasi ulang dengan data nyata sebelum digunakan untuk keputusan investasi.
"""

POSITIVE_ID = [
    "naik", "meningkat", "tumbuh", "pertumbuhan", "kuat", "menguat", "membaik",
    "bagus", "positif", "untung", "laba", "profit", "besar", "tinggi", "cemerlang",
    "gemilang", "pemulihan", "recovery", "rebound", "optimis", "optimisme",
    "kinerja baik", "dukungan", "mendukung", "insentif", "stimulus", "ekspansi",
    "perluasan", "investasi", "arus masuk", "surplus", "super", "rekor",
    "tertinggi", "terbaik", "berhasil", "sukses", "melonjak", "meroket", "reli",
    "rally", "bangkit", "maju", "keuntungan", "deviden", "dividen", "apresiasi",
    "ekspor naik", "permintaan naik", "booming", "memuaskan", "solid", "stabil",
    "sehat", "likuid", "aman", "dinaikkan", "upgrade", "naikkan", "efisien",
    "efisiensi", "menguntungkan", "prospek cerah", "masa depan baik", "outperform",
    "beat", "beyond expect", "kinerja gemilang", "meroket", "melesat", "menguat",
    "cuan", "gain", "untung besar", "laba bersih naik", "pendapatan naik", "top line",
    "ricuh", "hebat", "positif", "surplus perdagangan", "cadangan meningkat",
]

NEGATIVE_ID = [
    "turun", "merosot", "jatuh", "anjlok", "melemah", "lemah", "buruk", "negatif",
    "rugi", "kerugian", "kecil", "rendah", "gagal", "penurunan", "depresiasi",
    "krisis", "resesi", "stagflasi", "deflasi", "monster", "bangkrut", "default",
    "gagal bayar", "skandal", "korupsi", "penipuan", "fraud", "tuntutan", "gugatan",
    "sanksi", "embargo", "perang", "konflik", "bencana", "banjir", "gempa",
    "ancaman", "risiko", "downgrade", "diturunkan", "melemahkan", "pecat", "phk",
    "pemecatan", "minus", "defisit", "beban", "utang tinggi", "kelangkaan", "kekurangan",
    "oversupply", "harga turun", "permintaan turun", "ekspor turun", "jual",
    "panic selling", "kecemasan", "ketakutan", "khawatir", "pesimis", "lesu",
    "stagnan", "macet", "terganggu", "merugikan", "ambruk", "melempem", "limbung",
    "sangsama", "menarik diri", "instabilitas", "turbulensi", "volatilitas tinggi",
    "sarat risiko", "headwind", "tekanan", "pressure", "tertekan", "anjlok",
    "jeblok", "runtuh", "collaps", "rugi besar", "laba turun", "pendapatan turun",
    "defisit apbn", "inflasi tinggi", "suku bunga naik", "kenaikan pajak", "pajak baru",
    "beban pajak", "regulasi ketat", "pelarangan", "larangan", "restriksi",
]

POSITIVE_EN = [
    "rise", "rises", "rising", "surge", "surges", "surged", "soar", "soared",
    "climb", "climbed", "gain", "gains", "gained", "increase", "increased", "growth",
    "strong", "strengthen", "strengthened", "improve", "improves", "improvement",
    "positive", "profit", "profits", "earnings", "record", "high", "best", "top",
    "outperform", "outperformed", "optimistic", "optimism", "recover", "recovery",
    "rebound", "support", "supports", "stimulus", "expansion", "invest", "investment",
    "inflow", "surplus", "upgrade", "upgraded", "solid", "stable", "healthy", "boost",
    "boosted", "rally", "momentum", "bull", "bullish", "beat", "beats", "above expectations",
    "dividend", "buyback", "strong demand", "record high", "all-time high", "soaring",
    "climbing", "gain", "winner", "bright", "promising", "accelerate", "expanding",
    "booming",
]

NEGATIVE_EN = [
    "fall", "falls", "falling", "drop", "drops", "dropped", "plunge", "plunged",
    "slump", "slumped", "decline", "declined", "weak", "weaken", "weakened", "negative",
    "loss", "losses", "low", "fail", "failed", "failure", "crisis", "recession",
    "downturn", "depreciation", "default", "bankrupt", "bankruptcy", "lawsuit",
    "sanctions", "embargo", "war", "conflict", "disaster", "flood", "earthquake",
    "threat", "risk", "downgrade", "downgraded", "cut", "cuts", "layoff", "layoffs",
    "fired", "dismiss", "deficit", "debt", "shortage", "oversupply", "selloff",
    "panic", "fear", "worry", "pessimistic", "stagnant", "disrupt", "disrupted",
    "hurt", "crash", "crashed", "withdraw", "instability", "volatility", "drag",
    "headwind", "pressure", "pressured", "under pressure", "plummet", "plummeted",
    "deteriorate", "deterioration", "weak demand", "tariff", "tariffs", "levy",
    "subprime", "bubble", "collapse", "collapsed", "trouble", "turmoil", "distress",
]

# kata negasi (pembalik sentimen jika muncul sebelum kata sentimen)
NEGATION_WORDS = ["tidak", "bukan", "kurang", "tanpa", "belum", "not", "no", "never",
                  "tidak lagi", "sedikit", "berkurang"]

# kata penguat (memperbesar magnitudo)
INTENSIFIERS = {"sangat": 1.5, "amat": 1.5, "jauh": 1.3, "sangat": 1.5,
                "very": 1.5, "extremely": 1.6, "significantly": 1.4,
                "considerably": 1.3, "menggemparkan": 1.6, "besar-besaran": 1.5}
