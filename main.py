# main.py
"""
Main entrypoint for Chananalysis Bot (Render-ready).
- Background polling Telegram (polling mode) to avoid webhook conflicts
- Scheduler sends report every morning 08:00 WIB and evening 18:00 WIB (UTC times configurable)
- Uses analyzer.generate_report() to build message
"""

import os
import threading
import time
import schedule
import logging
import asyncio
from datetime import datetime
from flask import Flask
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from analyzer import generate_report

# -------------------------
# Config from env
# -------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SCHEDULE_UTC_MORNING = os.getenv("SCHEDULE_UTC_MORNING", "01:00")  # 01:00 UTC == 08:00 WIB
SCHEDULE_UTC_EVENING = os.getenv("SCHEDULE_UTC_EVENING", "11:00")  # 11:00 UTC == 18:00 WIB
TOP_N = int(os.getenv("TOP_N", "5"))

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment variables")

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("chananalysis-main")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# -------------------------
# Telegram command handlers
# -------------------------
async def start_handler(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo 👋 Chananalysis bot aktif. Laporan dikirim jam 08:00 & 18:00 WIB.")

async def id_handler(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID: {update.message.chat_id}")

# -------------------------
# Telegram polling runner (background thread)
# -------------------------
def run_telegram_polling():
    async def _run():
        # ensure webhook removed to avoid conflict
        try:
            await bot.delete_webhook()
        except Exception:
            pass
        app_t = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        app_t.add_handler(CommandHandler("start", start_handler))
        app_t.add_handler(CommandHandler("id", id_handler))
        await app_t.initialize()
        await app_t.start()
        logger.info("Telegram polling started.")
        try:
            await app_t.updater.start_polling()
            await asyncio.Event().wait()
        finally:
            await app_t.stop()
            await app_t.shutdown()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.exception("Telegram polling ended: %s", e)

# -------------------------
# Send message util
# -------------------------
def send_text(text):
    try:
        bot.send_message(chat_id=int(TELEGRAM_CHAT_ID), text=text, parse_mode="Markdown", disable_web_page_preview=True)
        logger.info("Message sent.")
    except Exception as e:
        logger.exception("Failed to send message: %s", e)

# -------------------------
# Job: build + send report
# -------------------------
def job_send_reports():
    logger.info("Running analysis job...")
    try:
        report = generate_report(top_n=TOP_N)
        send_text(report)
        # optionally send short watchlist (top 3 lines)
        # quick parse: take first N bullet lines starting with '*' and containing 'Asing'
        lines = report.splitlines()
        watch = []
        for ln in lines:
            if ln.strip().startswith("*") and ("Asing" in ln or "Asing" in ln):
                watch.append(ln.strip())
            if len(watch) >= 3:
                break
        if watch:
            send_text("🔥 *Watchlist Alert (Top signals)*\n" + "\n".join(watch))
    except Exception as e:
        logger.exception("Daily job failed: %s", e)
        send_text(f"❌ Daily job failed: {e}")

# -------------------------
# Scheduler thread
# -------------------------
def scheduler_thread():
    schedule.clear()
    schedule.every().day.at(SCHEDULE_UTC_MORNING).do(job_send_reports)
    schedule.every().day.at(SCHEDULE_UTC_EVENING).do(job_send_reports)
    logger.info(f"Scheduler set: morning {SCHEDULE_UTC_MORNING} UTC, evening {SCHEDULE_UTC_EVENING} UTC")
    while True:
        schedule.run_pending()
        time.sleep(8)

# -------------------------
# Flask endpoints
# -------------------------
@app.route("/")
def index():
    return "Chananalysis Bot running."

# -------------------------
# Entry
# -------------------------
if __name__ == "__main__":
    # Start polling & scheduler in background threads
    t = threading.Thread(target=run_telegram_polling, daemon=True)
    t.start()
    s = threading.Thread(target=scheduler_thread, daemon=True)
    s.start()

    # Start Flask app (Render will run this via hypercorn/gunicorn or builtin)
    try:
        # Use hypercorn if present for production async safety
        from hypercorn.asyncio import serve
        from hypercorn.config import Config
        import asyncio
        config = Config()
        port = int(os.getenv("PORT", "10000"))
        config.bind = [f"0.0.0.0:{port}"]
        logger.info("Starting hypercorn server...")
        asyncio.run(serve(app, config))
    except Exception:
        logger.info("Starting Flask builtin server...")
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
