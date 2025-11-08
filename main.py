import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Bot
import schedule
import requests
import pandas as pd
from datetime import datetime

# ==========================================================
# 1️⃣  Baca Token dari Environment Variable (aman di Render)
# ==========================================================
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ TELEGRAM_TOKEN tidak ditemukan. Pastikan sudah ditambahkan di Environment Variables di Render.")
    exit(1)

bot = Bot(token=TOKEN)
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # nanti bisa diisi manual, opsional

# ==========================================================
# 2️⃣  Dummy Server agar Render mendeteksi port terbuka (Wajib utk Free Plan)
# ==========================================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully on Render Free Plan!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"🌐 Dummy web server aktif di port {port}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ==========================================================
# 3️⃣  Fungsi Analisis Foreign Flow (contoh sederhana dulu)
# ==========================================================
def get_foreign_accumulation():
    """
    Fungsi contoh untuk ambil data akumulasi asing.
    Nanti bisa diganti dengan scraping RTI / IDX secara real-time.
    """
    # Contoh dummy data (nanti bisa diganti API real)
    data = [
        {"kode": "BBCA", "foreign_buy": 520e9, "foreign_sell": 410e9},
        {"kode": "BBRI", "foreign_buy": 480e9, "foreign_sell": 450e9},
        {"kode": "BMRI", "foreign_buy": 330e9, "foreign_sell": 280e9},
        {"kode": "ASII", "foreign_buy": 270e9, "foreign_sell": 240e9},
    ]
    df = pd.DataFrame(data)
    df["net_buy"] = df["foreign_buy"] - df["foreign_sell"]
    df = df.sort_values("net_buy", ascending=False)
    return df

# ==========================================================
# 4️⃣  Fungsi Kirim Laporan ke Telegram
# ==========================================================
def send_daily_report():
    df = get_foreign_accumulation()
    report_lines = ["📊 *Laporan Akumulasi Asing Harian* 🇮🇩", ""]
    for i, row in df.iterrows():
        report_lines.append(
            f"• {row['kode']} — Net Buy: Rp{row['net_buy']/1e9:.1f} M"
        )
    report_lines.append("")
    report_lines.append(f"_Dikirim otomatis {datetime.now().strftime('%d %b %Y %H:%M WIB')}_")

    message = "\n".join(report_lines)
    try:
        if CHAT_ID:
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        else:
            print("Pesan belum dikirim ke Telegram karena CHAT_ID kosong.")
            print(message)
    except Exception as e:
        print(f"❌ Gagal kirim ke Telegram: {e}")

# ==========================================================
# 5️⃣  Jadwal Otomatis Jam 18:00 WIB
# ==========================================================
def schedule_job():
    schedule.every().day.at("11:00").do(send_daily_report)  # 11:00 UTC = 18:00 WIB
    print("🕕 Jadwal laporan harian aktif: setiap 18:00 WIB (11:00 UTC).")

    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=schedule_job, daemon=True).start()

# ==========================================================
# 6️⃣  Bot Siap Jalan
# ==========================================================
print("🤖 Chananalysis bot aktif dan berjalan di background...")
while True:
    time.sleep(10)
