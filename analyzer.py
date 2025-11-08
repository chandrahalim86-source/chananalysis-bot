import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ====================================================
# KONFIGURASI RTI DAN STOCKBIT
# ====================================================
RTI_EMAIL = os.getenv("RTI_EMAIL")
RTI_PASSWORD = os.getenv("RTI_PASSWORD")

RTI_LOGIN_URL = "https://access.rti.co.id/auth/login"
RTI_FOREIGN_URL = "https://rti.co.id/stock/foreign"

# ====================================================
# LOGIN RTI & FETCH DATA
# ====================================================
def fetch_rti_data(days=7):
    """Login ke RTI dan ambil data net buy/sell foreign untuk n hari ke belakang"""
    session = requests.Session()
    login_payload = {"email": RTI_EMAIL, "password": RTI_PASSWORD}

    r = session.post(RTI_LOGIN_URL, data=login_payload)
    if r.status_code != 200:
        raise Exception(f"Gagal login RTI: {r.text}")

    data = []
    for i in range(days):
        d = datetime.now() - timedelta(days=i)
        url = f"{RTI_FOREIGN_URL}?date={d:%Y-%m-%d}"
        res = session.get(url)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table tr")[1:]
            for row in rows:
                cols = [c.get_text(strip=True) for c in row.find_all("td")]
                if len(cols) >= 5:
                    try:
                        data.append({
                            "date": d.date(),
                            "symbol": cols[0],
                            "foreign_buy": float(cols[2].replace(",", "")),
                            "foreign_sell": float(cols[3].replace(",", "")),
                            "price": float(cols[4].replace(",", "")),
                        })
                    except:
                        continue
    return pd.DataFrame(data)

# ====================================================
# ANALISA AKUMULASI ASING
# ====================================================
def calculate_foreign_accumulation(df):
    """Hitung akumulasi asing dan rata-rata harga beli"""
    result = []
    for symbol, group in df.groupby("symbol"):
        group = group.sort_values("date", ascending=True)
        group["net_buy"] = group["foreign_buy"] - group["foreign_sell"]

        # 1️⃣ Total akumulasi asing 7 hari terakhir
        streak = (group["net_buy"] > 0).sum()

        # 2️⃣ Deteksi fase keluar asing (hari negatif berturut-turut)
        outflow_days = 0
        for val in group["net_buy"][::-1]:
            if val < 0:
                outflow_days += 1
            else:
                break

        if streak >= 2:  # minimal 2 hari akumulasi
            total_buy = group["foreign_buy"].sum()
            avg_price = (group["price"] * group["foreign_buy"]).sum() / total_buy
            result.append({
                "symbol": symbol,
                "foreign_streak": streak,
                "outflow_days": outflow_days,
                "total_buy": total_buy,
                "avg_price": round(avg_price, 2)
            })
    return pd.DataFrame(result)

# ====================================================
# DATA STOCKBIT (PUBLIC)
# ====================================================
def fetch_stockbit_data(symbol):
    """Ambil data publik dari Stockbit"""
    try:
        url = f"https://stockbit.com/symbols/{symbol}"
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        last_price = soup.select_one(".price").get_text(strip=True).replace(",", "")
        volume = soup.select_one(".volume").get_text(strip=True).replace(",", "")
        return {
            "symbol": symbol,
            "last_price": float(last_price),
            "volume": int(volume)
        }
    except Exception:
        return {"symbol": symbol, "last_price": None, "volume": None}

# ====================================================
# SCORING SYSTEM (CHAN SCORE)
# ====================================================
def calculate_chan_score(row):
    """Skor gabungan akumulasi asing dan kestabilan harga"""
    streak_score = min(row["foreign_streak"], 7) / 7  # maksimal 7 hari akumulasi
    outflow_penalty = max(0, 1 - (row["outflow_days"] / 5))  # penalti jika asing keluar
    stability = 0.8 + 0.2 * outflow_penalty
    score = (streak_score * 0.5 + stability * 0.5) * 100
    return round(score, 1)

# ====================================================
# LAPORAN AKHIR
# ====================================================
def generate_report():
    df = fetch_rti_data()
    if df.empty:
        return "❌ Tidak ada data RTI hari ini."

    acc = calculate_foreign_accumulation(df)
    if acc.empty:
        return "Tidak ada saham dengan akumulasi asing signifikan minggu ini."

    reports = []
    for _, row in acc.iterrows():
        sb = fetch_stockbit_data(row["symbol"])
        score = calculate_chan_score(row)

        phase = "⚠️ Asing mulai keluar" if row["outflow_days"] >= 4 else "✅ Masih akumulasi"

        reports.append(
            f"📈 *{row['symbol']}*\n"
            f"• Akumulasi asing {row['foreign_streak']} hari\n"
            f"• Rata-rata beli asing: {row['avg_price']:,}\n"
            f"• Harga terakhir: {sb['last_price'] or '-'}\n"
            f"• Outflow: {row['outflow_days']} hari ({phase})\n"
            f"• ChanScore: {score}/100\n"
        )

    return "📊 *Laporan Akumulasi Asing (7 Hari)*\n\n" + "\n".join(reports)
