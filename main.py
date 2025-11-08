import requests
import schedule
import time
from datetime import datetime

TOKEN = "8488195293:AAE13Lzf11qQ4gc1dsH5uRHn0FvZo1nvxDg"
CHAT_ID = "1452360177"

def get_saham_analysis():
    data = [
        {"kode": "BBCA", "akumulasi": "+25M", "harga": "9,800"},
        {"kode": "BMRI", "akumulasi": "+18M", "harga": "6,300"},
        {"kode": "BBNI", "akumulasi": "+15M", "harga": "5,350"},
    ]
    msg = "📊 *Analisa Akumulasi Asing Hari Ini*\n"
    msg += f"🕕 {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
    for d in data:
        msg += f"💰 {d['kode']} — Akumulasi: {d['akumulasi']}, Harga: {d['harga']}\n"
    return msg

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def job():
    msg = get_saham_analysis()
    send_message(msg)
    print(f"[{datetime.now()}] Laporan saham dikirim!")

schedule.every().day.at("11:00").do(job)
send_message("🤖 Bot Chananalysis aktif di cloud!")

while True:
    schedule.run_pending()
    time.sleep(60)
