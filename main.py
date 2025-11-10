from flask import Flask, request
import threading, time, os, schedule
from telegram import Bot
from analyzer import generate_report

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

def send_report():
    report = generate_report()
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=report, parse_mode="Markdown")
    except Exception as e:
        print("Telegram send error:", e)

@app.route("/analyze", methods=["GET"])
def manual_trigger():
    threading.Thread(target=send_report).start()
    return "Manual analysis triggered successfully."

def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(30)

# Kirim otomatis jam 18:00 WIB (UTC 11:00)
schedule.every().day.at("11:00").do(send_report)
threading.Thread(target=scheduler_loop, daemon=True).start()

@app.route("/")
def index():
    return "Smart Adaptive Pro v3.0 Final Stable Running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
