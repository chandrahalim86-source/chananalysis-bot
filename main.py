import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask, request
import threading

# ===== Telegram Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif ✅\nSaya akan kirim analisa saham setiap jam 18:00 WIB.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID kamu: {chat_id}")

# ===== Flask App =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Chananalysis7878 aktif di Render 🚀"

# ===== Jalankan Telegram bot di background =====
def run_bot():
    async def main():
        application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("id", get_id))
        print("🤖 Telegram bot aktif dan polling dimulai...")
        await application.run_polling(close_loop=False)
    
    asyncio.run(main())

if __name__ == "__main__":
    # Jalankan Telegram bot di thread terpisah
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Jalankan Flask agar Render melihat port aktif
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
