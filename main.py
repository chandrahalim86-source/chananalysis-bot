from flask import Flask
import schedule
import time
import threading
from telegram import Bot
from analyzer import analyze_stock
import pandas as pd
import random

app = Flask(__name__)

# --- Telegram setup ---
BOT_TOKEN = "ISI_DENGAN_TOKEN_TELEGRAM_BOTMU"
CHAT_ID = "ISI_DENGAN_CHAT_ID_KAMU"
bot = Bot(token=BOT_TOKEN)

# --- Fungsi dummy untuk simulasi data ---
def get_stock_data(ticker):
    # Simulasi data historis 10 hari
    np.random.seed(hash(ticker) % 1000)
    data = {
        'Close': np.random.randint(1000, 4000, 10),
        'Volume': np.random.randint(1000000, 5000000, 10),
        'Foreign_Buy': np.random.randint(200000, 800000, 10),
        'Foreign_Sell': np.random.randint(200000, 800000, 10),
        'Retail_Buy': np.random.randint(200000, 800000, 10),
        'Retail_Sell': np.random.randint(200000, 800000, 10)
    }
    return pd.DataFrame(data)

# --- Fungsi utama analisa & kirim report ---
def run_analysis():
    tickers = ["BBCA", "TLKM", "BMRI", "BBRI", "ASII"]
    for t in tickers:
        df = get_stock_data(t)
        report = analyze_stock(df, t)
        bot.send_message(chat_id=CHAT_ID, text=report, parse_mode="Markdown")

# --- Scheduler otomatis ---
def schedule_jobs():
    schedule.every().day.at("08:00").do(run_analysis)
    schedule.every().day.at("18:00").do(run_analysis)

    while True:
        schedule.run_pending()
        time.sleep(60)

# Jalankan scheduler di thread terpisah
threading.Thread(target=schedule_jobs, daemon=True).start()

@app.route('/')
def home():
    return "📊 Stock Analyzer Bot aktif & siap kirim laporan setiap jam 08:00 & 18:00 WIB."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
