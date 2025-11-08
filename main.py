import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Konfigurasi dasar ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_URL = "https://foreign-flow-monitor.onrender.com"

app = Flask(__name__)
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


# === Jalankan Flask dan setup webhook ===
async def setup_webhook():
    webhook_url = f"{BOT_URL}/{TOKEN}"
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook diset ke: {webhook_url}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    asyncio.run(setup_webhook())
    app.run(host="0.0.0.0", port=port)
