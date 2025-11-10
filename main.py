import os
import logging
import schedule
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request
from analyzer import analyze_top_stocks
from telegram import Bot

# Telegram bot setup
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

# Environment configs
ANALYSIS_PERIOD = int(os.getenv("ANALYSIS_PERIOD", 15))
TOP_N = int(os.getenv("TOP_N", 20))
MIN_LIQUIDITY_VALUE = int(os.getenv("MIN_LIQUIDITY_VALUE", 10_000_000_000))
SCHEDULE_UTC_EVENING = os.getenv("SCHEDULE_UTC_EVENING", "11:00")  # 18:00 WIB

# Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def send_telegram_report():
    try:
        logging.info("Starting analysis...")
        report = analyze_top_stocks(
            days=ANALYSIS_PERIOD, top_n=TOP_N, min_liquidity=MIN_LIQUIDITY_VALUE
        )
        if report:
            bot.send_message(chat_id=CHAT_ID, text=report, parse_mode="Markdown")
            logging.info("Report sent successfully.")
        else:
            bot.send_message(chat_id=CHAT_ID, text="Tidak ada data tersedia hari ini.")
    except Exception as e:
        logging.error(f"Error in send_telegram_report: {e}")
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Terjadi error: {e}")

# Telegram webhook or manual trigger
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if update and "message" in update:
        text = update["message"].get("text", "")
        chat_id = update["message"]["chat"]["id"]

        if text.strip().lower() == "/analyze":
            bot.send_message(chat_id=chat_id, text="⏳ Sedang menganalisa...")
            report = analyze_top_stocks(
                days=ANALYSIS_PERIOD, top_n=TOP_N, min_liquidity=MIN_LIQUIDITY_VALUE
            )
            bot.send_message(chat_id=chat_id, text=report, parse_mode="Markdown")

    return "ok", 200

def scheduler_thread():
    schedule.every().day.at(SCHEDULE_UTC_EVENING).do(send_telegram_report)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=scheduler_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
