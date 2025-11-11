# main.py
import os
import logging
import asyncio
import threading
import time
import schedule
import requests
from datetime import datetime, timezone
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from hypercorn.asyncio import serve
from hypercorn.config import Config

from analyzer import analyze_foreign_flow

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ANALYSIS_PERIOD = int(os.getenv("ANALYSIS_PERIOD", "15"))
TOP_N = int(os.getenv("TOP_N", "20"))
MIN_LIQUIDITY_VALUE = float(os.getenv("MIN_LIQUIDITY_VALUE", "10000000000"))
SCHEDULE_UTC_TIME = os.getenv("SCHEDULE_UTC_TIME_EVENING", "11:00")

if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")
if not CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_CHAT_ID environment variable")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("chananalysis")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo 👋 Chananalysis Bot aktif.\n"
        "Saya akan kirim laporan harian akumulasi asing. Ketik /analyze untuk laporan sekarang."
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Sedang membuat laporan... Harap tunggu.")
    try:
        text, _ = analyze_foreign_flow(analysis_period=ANALYSIS_PERIOD, top_n=TOP_N, min_liq=MIN_LIQUIDITY_VALUE)
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal membuat laporan: {e}")

async def run_bot():
    logger.info("Starting Telegram bot (polling)...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("analyze", analyze_command))
    await app.initialize()
    await app.start()
    logger.info("Telegram bot running (polling).")
    try:
        await app.updater.start_polling(poll_interval=3)
        await asyncio.Event().wait()
    finally:
        await app.stop()
        await app.shutdown()

def run_bot_background():
    asyncio.run(run_bot())

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code != 200:
            logger.error("Telegram send failed: %s %s", r.status_code, r.text)
            return False
        return True
    except Exception as e:
        logger.exception("Telegram send exception: %s", e)
        return False

def run_daily_job():
    logger.info("Running daily job...")
    try:
        text, _ = analyze_foreign_flow()
        success = send_telegram_message(text)
        if success:
            logger.info("Daily report sent successfully.")
        else:
            logger.error("Daily report failed to send.")
    except Exception as e:
        logger.exception("Daily job failed: %s", e)
        send_telegram_message(f"❌ Daily job error: {e}")

def scheduler_thread():
    logger.info("Scheduler scheduled at %s UTC (~18:00 WIB)", SCHEDULE_UTC_TIME)
    schedule.clear()
    schedule.every().day.at(SCHEDULE_UTC_TIME).do(run_daily_job)
    while True:
        schedule.run_pending()
        time.sleep(5)

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Chananalysis Bot (Smart Adaptive Pro v3.0) is running."

def init_bot_and_scheduler():
    threading.Thread(target=run_bot_background, daemon=True).start()
    threading.Thread(target=scheduler_thread, daemon=True).start()
    logger.info("Bot and scheduler started in background threads.")

if __name__ == "__main__":
    init_bot_and_scheduler()
    config = Config()
    config.bind = ["0.0.0.0:10000"]
    asyncio.run(serve(app, config))
