# -*- coding: utf-8 -*-
"""
Fungsi seed dinonaktifkan — aplikasi hanya memakai berita asli dari
sumber RSS nasional & global (lihat config.SOURCES). Tidak ada berita contoh.
"""


def seed_if_empty(db=None, force=False):
    """Tidak lagi mengisi berita contoh. Selalu mengembalikan 0."""
    return 0
