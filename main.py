import os
import threading
import schedule
import time
import pytz
from datetime import datetime
from flask import Flask
from telegram import Bot
from analyzer import analyze_foreign_flow

# --- Flask app untuk "port binding" Render (agar tetap gratis) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Smart Adaptive Pro Analyzer is running — Free Render Mode"

# --- Environment Variables ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ANALYSIS_PERIOD = int(os.getenv("ANALYSIS_PERIOD", 15))
MIN_LIQUIDITY_VALUE = int(os.getenv("MIN_LIQUIDITY_VALUE", 10_000_000_000))
TOP_N = int(os.getenv("TOP_N", 20))

SCHEDULE_UTC_HOUR = int(os.getenv("SCHEDULE_UTC_HOUR", 11))  # 11 UTC = 18:00 WIB

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# --- Fungsi kirim laporan ---
def send_report():
    try:
        tz = pytz.timezone("Asia/Jakarta")
        now = datetime.now(tz)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⏳ Memulai analisa saham asing otomatis ({now.strftime('%Y-%m-%d %H:%M:%S')}) ...")

        report = analyze_foreign_flow(
            period=ANALYSIS_PERIOD,
            min_liquidity=MIN_LIQUIDITY_VALUE,
            top_n=TOP_N
        )

        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=report, parse_mode="Markdown")

        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="✅ Laporan selesai dikirim.\n\nGunakan /analyze kapan saja untuk manual run.")
    except Exception as e:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"❌ Error saat analisa otomatis: {e}")

# --- Scheduler otomatis setiap 18:00 WIB ---
def scheduler_job():
    schedule.every().day.at("11:00").do(send_report)  # UTC 11 = 18:00 WIB
    while True:
        schedule.run_pending()
        time.sleep(60)

# --- Telegram Command Handler (/analyze manual) ---
from telegram.ext import ApplicationBuilder, CommandHandler

async def analyze_command(update, context):
    await update.message.reply_text("⏳ Menjalankan analisa manual...")
    try:
        report = analyze_foreign_flow(
            period=ANALYSIS_PERIOD,
            min_liquidity=MIN_LIQUIDITY_VALUE,
            top_n=TOP_N
        )
        await update.message.reply_text(report, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi error: {e}")

def run_telegram_bot():
    app_tg = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("analyze", analyze_command))
    app_tg.run_polling()

# --- Jalankan paralel (scheduler + telegram bot) ---
def run_all():
    threading.Thread(target=scheduler_job, daemon=True).start()
    run_telegram_bot()

if __name__ == "__main__":
    print("⏰ Scheduler aktif setiap 11:00 UTC (~18:00 WIB)")
    print("🚀 Smart Adaptive Pro Analyzer aktif")

    # Jalankan bot & scheduler di thread terpisah
    threading.Thread(target=run_all, daemon=True).start()

    # Jalankan Flask agar Render melihat port aktif
    app.run(host="0.0.0.0", port=10000)
