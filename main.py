import os
import logging
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ------------------------------
# KONFIGURASI
# ------------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8488195293:AAE13Lzf11qQ4gc1dsH5uRHn0FvZo1nvxDg")

# ------------------------------
# LOGGING
# ------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------------
# HANDLER TELEGRAM
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo 👋, saya *Chananalysis Bot*!\nKetik /id untuk melihat chat ID kamu.",
        parse_mode="Markdown"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID kamu adalah: `{chat_id}`", parse_mode="Markdown")

# ------------------------------
# INISIALISASI TELEGRAM BOT (ASYNC)
# ------------------------------
async def run_bot():
    logger.info("Memulai Chananalysis Bot...")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_id))

    await application.initialize()
    await application.start()
    logger.info("Bot Telegram berjalan (polling aktif).")

    # Loop polling
    try:
        await application.updater.start_polling(poll_interval=3)
        await asyncio.Event().wait()  # biar tetap jalan
    finally:
        await application.stop()
        await application.shutdown()

# ------------------------------
# FLASK APP (ASYNC)
# ------------------------------
app = Flask(__name__)

@app.route("/")
async def index():
    return "✅ Chananalysis Bot sedang berjalan dengan async polling!"

# ------------------------------
# MAIN ENTRY POINT
# ------------------------------
if __name__ == "__main__":
    # Jalankan Flask di event loop utama
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Jalankan bot di background task
    loop.create_task(run_bot())

    # Jalankan Flask server
    app.run(host="0.0.0.0", port=10000)
