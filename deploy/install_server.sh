#!/usr/bin/env bash
# ============================================================
#  Install & jalankan Pasar Intel di VPS Linux (Ubuntu/Debian)
#  Jalankan sebagai root:  sudo bash install_server.sh
# ============================================================
set -euo pipefail

APP_DIR=/opt/pasar-intel
SERVICE=pasar-intel.service

echo "[1/5] Update paket & install dependensi sistem..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip curl

echo "[2/5] Siapkan folder aplikasi..."
# Salin kode ke /opt (jalankan dari folder deploy => sumber di ../)
SRC="$(cd "$(dirname "$0")/.." && pwd)"
if [ -d "$APP_DIR" ] && [ -f "$APP_DIR/main.py" ]; then
  echo "  folder $APP_DIR sudah ada, menyalin ulang file kode..."
  rsync -a --delete --exclude 'data/' --exclude 'venv/' "$SRC/" "$APP_DIR/"
else
  mkdir -p "$APP_DIR"
  rsync -a --exclude 'data/' --exclude 'venv/' "$SRC/" "$APP_DIR/"
fi

# pengguna khusus untuk menjalankan layanan
id -u pasarintel &>/dev/null || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin pasarintel
mkdir -p "$APP_DIR/data"
chown -R pasarintel:pasarintel "$APP_DIR"

echo "[3/5] Virtual env & install dependensi Python..."
cd "$APP_DIR"
python3 -m venv venv
./venv/bin/pip install --upgrade pip setuptools wheel
./venv/bin/pip install -r requirements.txt

echo "[4/5] Pasang systemd service..."
cp "$SRC/deploy/pasar-intel.service" /etc/systemd/system/$SERVICE
systemctl daemon-reload
systemctl enable $SERVICE
systemctl start $SERVICE

echo "[5/5] Verifikasi..."
sleep 5
if curl -fsS http://127.0.0.1:8000/api/health >/dev/null; then
  echo "  [OK] Aplikasi berjalan: http://<IP-VPS>:8000"
else
  echo "  [PERINGATAN] Cek status: systemctl status $SERVICE"
fi

echo
echo "Selesai! Untuk membuka dari luar, pastikan port 8000 terbuka di firewall:"
echo "  ufw allow 8000/tcp  (jika pakai ufw)"
echo "  atau buka port 8000 di panel penyedia VPS Anda."
