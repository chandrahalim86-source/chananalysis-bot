import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import pytz
import schedule
import time
import threading

from analyzer import analyze_top_stocks
from data_fetcher import get_stock_list

# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ANALYSIS_PERIOD = int(os.getenv("ANALYSIS_PERIOD", 15))
TOP_N = int(os.getenv("TOP_N", 20))
MIN_LIQUIDITY_VALUE = int(os.getenv("MIN_LIQUIDITY_VALUE", 10_000_000_000))
SCHEDULE_UTC_EVENING = os.getenv("SCHEDULE_UTC_EVENING", "11:00")  # 18:00 WIB default

# ==================================================
# CORE TELEGRAM FUNCTION
# ==================================================
async def send_report(context: ContextTypes.DEFAULT_TYPE):
    """Mengambil saham, analisa, dan kirim laporan ke Telegram"""
    try:
        symbols = get_stock_list()
        report = analyze_top_stocks(
            symbols,
            period=ANALYSIS_PERIOD,
            min_liquidity=MIN_LIQUIDITY_VALUE,
            top_n=TOP_N
        )

        timestamp = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
        message = f"*Laporan Akumulasi Asing ({ANALYSIS_PERIOD} Hari)*\nGenerated: {timestamp}\n{report}"

        await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        print("✅ Report sent successfully at", timestamp)
    except Exception as e:
        print("❌ Error sending report:", e)


async def analyze_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perintah manual untuk analisa instan via Telegram"""
    await update.message.reply_text("⏳ Sedang menganalisa saham... Mohon tunggu sebentar.")
    try:
        symbols = get_stock_list()
        report = analyze_top_stocks(
            symbols,
            period=ANALYSIS_PERIOD,
            min_liquidity=MIN_LIQUIDITY_VALUE,
            top_n=TOP_N
        )

        timestamp = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
        message = f"*Laporan Akumulasi Asing ({ANALYSIS_PERIOD} Hari)*\nGenerated: {timestamp}\n{report}"

        await update.message.reply_text(message, parse_mode="Markdown")
        print("✅ Manual /analyze report sent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi error: {e}")


def run_schedule(application):
    """Scheduler untuk menjalankan analisa otomatis"""
    hour, minute = map(int, SCHEDULE_UTC_EVENING.split(":"))
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
        lambda: asyncio.run_coroutine_threadsafe(
            send_report(application),
            application.loop
        )
    )

    print(f"⏰ Scheduler aktif setiap {SCHEDULE_UTC_EVENING} UTC (~18:00 WIB)")

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    """Entry utama program"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("analyze", analyze_now))

    # Jalankan scheduler otomatis (terpisah thread)
    thread = threading.Thread(target=run_schedule, args=(application,))
    thread.daemon = True
    thread.start()

    print("🚀 Smart Adaptive Pro v2.3 Analyzer aktif")
    application.run_polling()


if __name__ == "__main__":
    main()
