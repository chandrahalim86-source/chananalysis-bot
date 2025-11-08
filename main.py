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

# ------------------------------
# KONFIGURASI
# ------------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SCHEDULE_UTC_TIME = os.getenv("SCHEDULE_UTC_TIME", "01:00")  # 01:00 UTC = 08:00 WIB

if not TOKEN:
    raise RuntimeError("⚠️ Missing TELEGRAM_BOT_TOKEN in environment variables")
if not CHAT_ID:
    raise RuntimeError("⚠️ Missing TELEGRAM_CHAT_ID in environment variables")

# ------------------------------
# LOGGING
# ------------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("chananalysis")

# ------------------------------
# HANDLER TELEGRAM
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo 👋, saya *Chananalysis Bot*!\n"
        "Saya akan kirimkan laporan akumulasi asing tiap hari jam 08:00 WIB.\n"
        "Ketik /id untuk lihat chat ID kamu.",
        parse_mode="Markdown"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID kamu: `{chat_id}`", parse_mode="Markdown")

# ------------------------------
# ASYNC TELEGRAM BOT
# ------------------------------
async def run_bot():
    logger.info("🚀 Memulai Chananalysis Bot...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))

    await app.initialize()
    await app.start()
    logger.info("✅ Bot Telegram aktif (polling).")

    # Jalankan polling terus-menerus
    try:
        await app.updater.start_polling(poll_interval=3)
        await asyncio.Event().wait()  # tetap jalan
    finally:
        await app.stop()
        await app.shutdown()

# ------------------------------
# DAILY JOB (dijalankan oleh schedule)
# ------------------------------
def run_daily_job():
    now = datetime.now(timezone.utc)
    logger.info("🕗 Menjalankan job harian %s", now)

    try:
        # --- nanti diganti dengan logic analyzer real ---
        report_text = (
            "📊 *Laporan Harian Chananalysis*\n\n"
            "Data masih placeholder — modul analyzer/scraper belum diaktifkan.\n"
            f"Timestamp: {datetime.now():%Y-%m-%d %H:%M WIB}"
        )

        send_message(report_text)
    except Exception as e:
        logger.exception("❌ Gagal menjalankan job harian: %s", e)

def send_message(text):
    """Kirim pesan langsung ke Telegram tanpa async."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code != 200:
            logger.error("Gagal kirim Telegram message: %s - %s", r.status_code, r.text)
        else:
            logger.info("✅ Pesan terkirim ke Telegram.")
    except Exception as e:
        logger.exception("Gagal kirim pesan Telegram: %s", e)

# ------------------------------
# SCHEDULER THREAD
# ------------------------------
def scheduler_thread():
    logger.info("🗓️ Menjadwalkan laporan harian jam %s UTC (~08:00 WIB)", SCHEDULE_UTC_TIME)
    schedule.clear()
    schedule.every().day.at(SCHEDULE_UTC_TIME).do(run_daily_job)

    while True:
        schedule.run_pending()
        time.sleep(5)

# ------------------------------
# FLASK APP
# ------------------------------
app = Flask(__name__)

@app.route("/")
async def index():
    return "✅ Chananalysis Bot aktif dan siap kirim laporan harian."

# ------------------------------
# ENTRY POINT
# ------------------------------
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Jalankan bot di background task
    loop.create_task(run_bot())

    # Jalankan scheduler di thread terpisah
    threading.Thread(target=scheduler_thread, daemon=True).start()

    # Jalankan Flask (agar Render tetap aktif)
    config = Config()
    config.bind = ["0.0.0.0:10000"]
    loop.run_until_complete(serve(app, config))
