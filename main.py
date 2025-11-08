import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests, pandas as pd, schedule, threading, time, datetime

# ----------------------------
# KONFIGURASI
# ----------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # otomatis diset oleh Render
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # isi manual nanti

app = Flask(__name__)

# ----------------------------
# TELEGRAM BOT
# ----------------------------
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot RTI-Stockbit aktif!\nAnda akan menerima laporan harian jam 08:00 WIB.")

application.add_handler(CommandHandler("start", start))

# ----------------------------
# LAPORAN HARIAN
# ----------------------------
def get_daily_report():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"BBRI": 82, "BBCA": 79, "ASII": 68, "TLKM": 71, "ICBP": 88}
    df = pd.DataFrame(list(data.items()), columns=["Saham", "Score"])
    df.sort_values("Score", ascending=False, inplace=True)
    report = f"📅 Laporan Saham {now}\n\n" + df.to_string(index=False)
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": report})

def scheduler_loop():
    schedule.every().day.at("08:00").do(get_daily_report)
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=scheduler_loop, daemon=True).start()

# ----------------------------
# FLASK WEBHOOK
# ----------------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "ok", 200

@app.before_first_request
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set ke {webhook_url}")

@app.route("/")
def index():
    return "Bot RTI-Stockbit aktif dan menunggu update Telegram."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
