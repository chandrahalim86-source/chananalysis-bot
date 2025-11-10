import os
import pytz
import pandas as pd
import random
from datetime import datetime, time
from telegram import Bot
from telegram.ext import Application, CommandHandler
from analyzer import analyze_foreign_flow

# --- Environment Variables ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANALYSIS_PERIOD = int(os.getenv("ANALYSIS_PERIOD", 15))
TOP_N = int(os.getenv("TOP_N", 20))
SCHEDULE_UTC_EVENING = os.getenv("SCHEDULE_UTC_EVENING", "11:00")  # 18:00 WIB = 11:00 UTC
TIMEZONE = pytz.timezone("Asia/Jakarta")

bot = Bot(token=TELEGRAM_TOKEN)

# --- Dummy fetcher (ganti nanti ke data asli) ---
def fetch_data():
    symbols = ["BBCA", "TLKM", "ASII", "BBRI", "UNVR", "BMRI", "BBNI", "CPIN", "ICBP", "INDF",
               "ANTM", "ADRO", "MDKA", "UNTR", "PGAS", "PTBA", "SIDO", "AKRA", "TPIA", "BRIS"]
    data = {}
    for s in symbols:
        df = pd.DataFrame({
            "close": [random.randint(2000, 8000) for _ in range(ANALYSIS_PERIOD)],
            "foreign_net": [random.uniform(-8e7, 8e7) for _ in range(ANALYSIS_PERIOD)],
            "retail_net": [random.uniform(-8e7, 8e7) for _ in range(ANALYSIS_PERIOD)],
            "value": [random.uniform(5e9, 2e10) for _ in range(ANALYSIS_PERIOD)],
        })
        data[s] = df
    return data

# --- Format laporan ---
def format_report(results):
    header = f"📊 *Laporan Akumulasi Asing ({ANALYSIS_PERIOD} Hari)*\nGenerated: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S WIB')}\nTop {TOP_N} Saham Likuid\n\n"
    body = ""
    for r in results[:TOP_N]:
        section = (
            f"*{r['symbol']}* — Asing jual {r['foreign_sell_days']}/{r['period']} hari "
            f"({'Distribusi' if r['net_foreign'] < 0 else 'Akumulasi'})\n"
            f"Rata-rata beli/jual asing: Rp {r['avg_foreign']:,}\n"
            f"Harga terakhir: Rp {r['last_price']:,} ({r['price_change']}%)\n"
            f"Net Asing ({r['period']}d): Rp {r['net_foreign']/1e6:.1f}M | Ritel: Rp {r['net_retail']/1e6:.1f}M\n"
            f"Likuiditas avg: Rp {r['avg_value']/1e9:.1f}B\n"
            f"ChanScore: {r['chscore']}/100 → {r['trend']}\n"
            f"🔄 Divergensi: {r['divergensi']} (corr={r['corr']})\n"
            f"📈 Kesimpulan: {r['kesimpulan']}\n\n"
        )
        body += section
    return header + body.strip()

# --- Analisa dan kirim laporan ---
async def send_report():
    data = fetch_data()
    results = analyze_foreign_flow(data, period=ANALYSIS_PERIOD)
    report = format_report(results)
    await bot.send_message(chat_id=CHAT_ID, text=report, parse_mode="Markdown")

async def analyze_command(update, context):
    await send_report()
    await update.message.reply_text("✅ Analisa manual selesai — laporan sudah dikirim.", parse_mode="Markdown")

def schedule_jobs(app):
    hour, minute = map(int, SCHEDULE_UTC_EVENING.split(":"))
    app.job_queue.run_daily(send_report, time=time(hour=hour, minute=minute, tzinfo=pytz.UTC))

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("analyze", analyze_command))
    schedule_jobs(app)
    app.run_polling()

if __name__ == "__main__":
    main()
