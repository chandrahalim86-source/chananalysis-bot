import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading

# ==== Telegram Command Functions ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif ✅\nSaya akan kirim analisa saham setiap jam 18:00 WIB.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID kamu: {chat_id}")

# ==== Telegram Bot Setup ====

def run_bot():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.run_polling()

# ==== Flask App (untuk Render agar port terbuka) ====

server = Flask(__name__)

@server.route("/")
def home():
    return "Bot Chananalysis7878 aktif di Render 🚀"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
