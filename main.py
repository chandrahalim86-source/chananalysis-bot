import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Setup logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# === Konfigurasi dasar ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_URL = "https://foreign-flow-monitor.onrender.com"  # Ganti jika nama service berubah
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{BOT_URL}{WEBHOOK_PATH}"

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()


# === Command Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hai! Bot Chananalysis aktif.\nSaya akan mengirim analisa saham setiap jam 18:00 WIB."
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID kamu: {update.effective_chat.id}")


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("id", get_id))


# === Flask Routes ===
@app.route("/", methods=["GET"])
def home():
    return "✅ Chananalysis Bot aktif dan webhook siap!"


@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    """Terima update dari Telegram"""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return "Error", 500
    return "OK", 200


# === Start-up Function ===
async def setup_webhook():
    # Hapus webhook lama dan set yang baru
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"✅ Webhook set ke {WEBHOOK_URL}")


def main():
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_webhook())

    # Jalankan Flask di foreground
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
