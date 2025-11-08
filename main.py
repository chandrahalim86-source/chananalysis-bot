import os
import asyncio
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Konfigurasi dasar ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_URL = "https://foreign-flow-monitor.onrender.com"

app = Flask(__name__)

# === Inisialisasi aplikasi Telegram ===
application = Application.builder().token(TOKEN).build()


# === Command handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot Chananalysis7878 aktif!\nSaya akan kirim analisa saham jam 18:00 WIB setiap hari.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID kamu: {update.message.chat_id}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("id", get_id))


# === Web routes ===
@app.route("/", methods=["GET"])
def index():
    return "✅ Chananalysis7878 aktif dan webhook siap!"


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook_update():
    """Terima update dari Telegram"""
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200


# === Jalankan bot di background thread ===
def run_bot():
    asyncio.run(start_bot())


async def start_bot():
    await application.initialize()
    await application.start()
    webhook_url = f"{BOT_URL}/{TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook aktif di {webhook_url}")
    await application.updater.start_polling()
    await application.wait_until_closed()


if __name__ == "__main__":
    # Jalankan Telegram bot di thread terpisah
    threading.Thread(target=run_bot, daemon=True).start()

    # Jalankan Flask server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
