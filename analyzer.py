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
def fetch_rti_data():
    """Login ke RTI dan ambil data net buy/sell foreign"""
    session = requests.Session()
    login_payload = {"email": RTI_EMAIL, "password": RTI_PASSWORD}

    r = session.post(RTI_LOGIN_URL, data=login_payload)
    if r.status_code != 200:
        raise Exception(f"Gagal login RTI: {r.text}")

    data = []
    for i in range(7):  # periode 7 hari (ideal balance)
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
    df = pd.DataFrame(data)
    return df

# ====================================================
# ANALISA AKUMULASI ASING
# ====================================================
def calculate_foreign_accumulation(df):
    """Hitung akumulasi asing, rata-rata harga beli, dan volume"""
    result = []
    for symbol, group in df.groupby("symbol"):
        group = group.sort_values("date", ascending=True)
        group["net_buy"] = group["foreign_buy"] - group["foreign_sell"]
        streak = (group["net_buy"] > 0).sum()

        # Minimal 3 hari berturut-turut akumulasi untuk dianggap signifikan
        if streak >= 3:
            total_buy = group["foreign_buy"].sum()
            total_sell = group["foreign_sell"].sum()
            avg_price = (group["price"] * group["foreign_buy"]).sum() / total_buy

            result.append({
                "symbol": symbol,
                "foreign_streak": streak,
                "total_buy": total_buy,
                "total_sell": total_sell,
                "avg_price": round(avg_price, 2),
                "last_price": group["price"].iloc[-1],
                "net_buy": total_buy - total_sell
            })
    return pd.DataFrame(result)

# ====================================================
# FETCH DATA STOCKBIT (untuk validasi volume / harga)
# ====================================================
def fetch_stockbit_data(symbol):
    """Ambil data publik dari Stockbit"""
    try:
        url = f"https://stockbit.com/symbols/{symbol}"
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        price_el = soup.select_one(".price")
        volume_el = soup.select_one(".volume")

        if not price_el or not volume_el:
            return {"symbol": symbol, "last_price": None, "volume": None}

        last_price = float(price_el.get_text(strip=True).replace(",", ""))
        volume = int(volume_el.get_text(strip=True).replace(",", ""))
        return {"symbol": symbol, "last_price": last_price, "volume": volume}
    except Exception:
        return {"symbol": symbol, "last_price": None, "volume": None}

# ====================================================
# SCORING SYSTEM (v2.1 Optimal)
# ====================================================
def calculate_chan_score(row):
    foreign_streak = min(row["foreign_streak"], 7) / 7
    net_ratio = row["net_buy"] / max(row["total_buy"] + row["total_sell"], 1)
    price_stability = 1 - abs(row["last_price"] - row["avg_price"]) / row["avg_price"]
    volume_strength = 1.0  # placeholder; real value dari Stockbit bisa ditambahkan nanti

    base_score = (
        (0.35 * foreign_streak) +
        (0.20 * net_ratio) +
        (0.25 * price_stability) +
        (0.15 * volume_strength)
    ) * 100

    # Bonus atau penalti jika asing & ritel berlawanan arah
    sentiment_adjustment = 10 if row["net_buy"] > 0 else -10

    score = base_score + sentiment_adjustment
    return round(max(min(score, 100), 0), 1)

# ====================================================
# INTERPRETASI SKOR
# ====================================================
def interpret_score(score):
    if score >= 85:
        return "🚀 Strong Accumulation (Strong Buy / Hold Aggressive)"
    elif score >= 70:
        return "🟢 Moderate Accumulation (Hold / Add on Weakness)"
    elif score >= 55:
        return "⚪ Neutral (Early Watch / Small Entry)"
    elif score >= 40:
        return "🟠 Caution – Possible Distribution (Reduce / Tight Stop)"
    else:
        return "🔴 Strong Distribution (Sell on Strength / Avoid Entry)"

# ====================================================
# CUT LOSS & REKOMENDASI LEVEL
# ====================================================
def determine_trade_levels(row):
    last_price = row["last_price"]
    avg_price = row["avg_price"]

    if row["net_buy"] > 0:  # Asing akumulasi
        buy_zone = round(avg_price * 0.97, 2)
        cut_loss = round(avg_price * 0.93, 2)
        return f"💰 Buy Zone: {buy_zone} | ⛔ Cut Loss: {cut_loss}"
    else:  # Asing jualan
        sell_zone = round(avg_price * 1.03, 2)
        cut_loss = round(avg_price * 1.07, 2)
        return f"💸 Sell Zone: {sell_zone} | ⛔ Cut Loss if > {cut_loss}"

# ====================================================
# GENERATE FINAL REPORT
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
        sentiment = interpret_score(score)
        trade_levels = determine_trade_levels(row)

        reports.append(
            f"📈 *{row['symbol']}*\n"
            f"ChanScore: *{score}/100* — {sentiment}\n"
            f"Asing beli: {row['total_buy']:,} | Jual: {row['total_sell']:,}\n"
            f"Rata-rata beli asing: {row['avg_price']:,}\n"
            f"Harga terakhir: {sb['last_price'] or row['last_price']:,}\n"
            f"{trade_levels}\n"
        )

    return "📊 *Laporan Akumulasi Asing (7 Hari)*\n\n" + "\n".join(reports)
