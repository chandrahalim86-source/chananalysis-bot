import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# =========================================
# SMART ADAPTIVE PRO V3.0 FINAL STABLE
# =========================================

def fetch_foreign_data():
    """
    Ambil 15 hari data foreign net buy/sell dari RTI (atau fallback Stockbit)
    """
    try:
        url = "https://api.rti.co.id/api/foreign-accumulation"
        response = requests.get(url, timeout=10)
        data = response.json()["data"]
        df = pd.DataFrame(data)
        df["foreign_net"] = df["buy_value"] - df["sell_value"]
        df["date"] = pd.to_datetime(df["date"])
        df = df.groupby("code").tail(15)
        return df
    except Exception as e:
        print("Fallback source triggered:", e)
        # fallback dummy (replace later if needed)
        cols = ["code", "date", "foreign_net", "price", "volume"]
        return pd.DataFrame(columns=cols)


def calculate_chan_score(df):
    """
    Hitung skor akumulasi asing & kekuatan tren
    """
    if df.empty:
        return pd.DataFrame()

    result = []
    for code, data in df.groupby("code"):
        data = data.sort_values("date")
        foreign_acc = data["foreign_net"].sum()
        vol = data["volume"].sum() if "volume" in data else 1
        last_price = data["price"].iloc[-1] if "price" in data else np.nan

        avg_foreign = data["foreign_net"].mean()
        trend_strength = np.sign(avg_foreign) * np.log1p(abs(avg_foreign)) / 10
        score = np.clip((foreign_acc / vol) * 100 + trend_strength * 50, -100, 100)

        result.append({
            "code": code,
            "foreign_acc": foreign_acc,
            "chan_score": round(score, 2),
            "price": last_price
        })
    return pd.DataFrame(result)


def interpret_score(row):
    """
    Buat kesimpulan otomatis berbasis skor dan arah akumulasi
    """
    code = row["code"]
    score = row["chan_score"]
    acc = row["foreign_acc"]
    price = row["price"]

    if score > 50:
        note = "Asing akumulasi kuat, potensi uptrend lanjut."
    elif 20 < score <= 50:
        note = "Akumulasi moderat, tren mulai positif."
    elif -20 <= score <= 20:
        note = "Netral, tunggu konfirmasi arah harga & asing."
    elif -50 <= score < -20:
        note = "Distribusi ringan, waspadai potensi koreksi."
    else:
        note = "Distribusi asing signifikan, risiko koreksi tinggi."

    kesimpulan = (
        f"📊 *{code}*\n"
        f"💰 Foreign Acc: {acc:,.0f}\n"
        f"📈 ChanScore: {score}\n"
        f"💵 Harga akhir: Rp{price:,.0f}\n\n"
        f"📋 Kesimpulan: {note}\n"
        "━━━━━━━━━━━━━━━\n"
    )
    return kesimpulan


def generate_report():
    """
    Analisis 20 saham foreign accumulation terbesar 15 hari terakhir
    """
    raw = fetch_foreign_data()
    if raw.empty:
        return "❌ Gagal mengambil data foreign accumulation."

    scored = calculate_chan_score(raw)
    top20 = scored.sort_values("foreign_acc", ascending=False).head(20)

    report = "📈 *LAPORAN FOREIGN ACCUMULATION – 15 HARI TERAKHIR*\n━━━━━━━━━━━━━━━\n\n"
    for _, row in top20.iterrows():
        report += interpret_score(row) + "\n"
    report += f"📅 Update: {datetime.now().strftime('%d %b %Y %H:%M')} WIB"
    return report
