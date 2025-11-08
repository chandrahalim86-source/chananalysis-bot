import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Telegram bot setup ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_URL = f"https://foreign-flow-monitor.onrender.com"

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()


# === Command Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif ✅\nSaya akan kirim analisa saham setiap jam 18:00 WIB.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID kamu: {update.message.chat_id}")


# Tambahkan handler ke bot
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("id", get_id))


# === Flask Routes ===
@app.route("/")
def home():
    return "🤖 Chananalysis7878 aktif dengan Webhook di Render!"


@app.route(f"/{TOKEN}", methods=["POST"])
async def telegram_webhook():
    """Webhook endpoint untuk menerima update dari Telegram"""
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "OK", 200


# === Setup webhook saat server mulai ===
@app.before_first_request
def init_webhook():
    import asyncio
    loop = asyncio.get_event_loop()
    webhook_url = f"{BOT_URL}/{TOKEN}"
    loop.run_until_complete(application.bot.set_webhook(url=webhook_url))
    print(f"✅ Webhook diset di: {webhook_url}")


# === Run Flask server ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
