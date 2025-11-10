import os
import asyncio
from datetime import datetime
import pytz
from telegram import Bot
from analyzer import StockAnalyzer
import schedule
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PERIOD = int(os.getenv("ANALYSIS_PERIOD", 15))
TOP_N = int(os.getenv("TOP_N", 20))
MIN_LIQUIDITY = int(os.getenv("MIN_LIQUIDITY_VALUE", 10_000_000_000))
SCHEDULE_UTC_EVENING = int(os.getenv("SCHEDULE_UTC_EVENING", 11))  # 18:00 WIB = 11:00 UTC

bot = Bot(token=TELEGRAM_TOKEN)
analyzer = StockAnalyzer(period_days=PERIOD, min_liquidity=MIN_LIQUIDITY)

async def send_analysis():
    now = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    header = f"*Laporan Akumulasi Asing ({PERIOD} Hari)*\nGenerated: {now}\n\n"
    report = analyzer.analyze_top_stocks(top_n=TOP_N)
    await bot.send_message(chat_id=CHAT_ID, text=header + report, parse_mode="Markdown")

def job():
    asyncio.run(send_analysis())

def run_scheduler():
    schedule.every().day.at("11:00").do(job)  # 11:00 UTC = 18:00 WIB
    print("Scheduler aktif untuk jam 18:00 WIB.")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    run_scheduler()
