import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Konfigurasi dasar ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_URL = "https://foreign-flow-monitor.onrender.com"

# Inisialisasi Flask & Telegram
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()


# === Command handler ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot Chananalysis7878 aktif!\nSaya akan kirim analisa saham jam 18:00 WIB setiap hari.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID kamu: {update.message.chat_id}")


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("id", get_id))


# === Webhook handler ===
@app.route("/", methods=["GET"])
def index():
    return "✅ Chananalysis7878 aktif dan siap menerima webhook dari Telegram!"


@app.route(f"/{TOKEN}", methods=["POST"])
async def receive_update():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "OK", 200


# === Jalankan Flask + setup webhook di startup ===
async def setup_webhook():
    webhook_url = f"{BOT_URL}/{TOKEN}"
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook diset ke: {webhook_url}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_webhook())
    app.run(host="0.0.0.0", port=port)
