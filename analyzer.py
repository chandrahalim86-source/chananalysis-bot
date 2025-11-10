import pandas as pd
import numpy as np

def analyze_stock(data, ticker):
    """
    Analisis pergerakan asing & ritel selama 10 hari terakhir.
    Menghasilkan sinyal beli/jual adaptif berbasis tren & akumulasi.
    """

    # --- Parameter dasar ---
    PERIOD = 10
    MA_WINDOW = 5
    STRONG_ACCUM_THRESHOLD = 0.6
    STRONG_DISTRIB_THRESHOLD = 0.6
    DIVERGENCE_THRESHOLD = 0.7

    # --- Data preparation ---
    df = data.tail(PERIOD).copy()
    df['Foreign_Buy_Sell'] = df['Foreign_Buy'] - df['Foreign_Sell']
    df['Retail_Buy_Sell'] = df['Retail_Buy'] - df['Retail_Sell']

    avg_price = round(df['Close'].mean(), 2)
    avg_foreign_buy = round(df[df['Foreign_Buy_Sell'] > 0]['Close'].mean(), 2)
    avg_foreign_sell = round(df[df['Foreign_Buy_Sell'] < 0]['Close'].mean(), 2)

    net_foreign = df['Foreign_Buy_Sell'].sum()
    net_retail = df['Retail_Buy_Sell'].sum()

    up_days = (df['Foreign_Buy_Sell'] > 0).sum()
    down_days = (df['Foreign_Buy_Sell'] < 0).sum()
    ratio_buy_days = up_days / PERIOD

    last_price = df['Close'].iloc[-1]
    price_change_pct = (last_price - avg_price) / avg_price * 100
    volume_ratio = round(df['Volume'].iloc[-1] / df['Volume'].mean() * 100, 1)

    # --- Tren harga ---
    df['MA5'] = df['Close'].rolling(MA_WINDOW).mean()
    trend = "Uptrend" if df['Close'].iloc[-1] > df['MA5'].iloc[-1] else "Downtrend"

    # --- Divergensi Asing vs Ritel ---
    corr = df['Foreign_Buy_Sell'].corr(df['Retail_Buy_Sell'])
    divergence = "Yes" if corr < -DIVERGENCE_THRESHOLD else "No"

    # --- Scoring system ---
    score = 0
    if ratio_buy_days >= STRONG_ACCUM_THRESHOLD:
        score += 3
    elif ratio_buy_days >= 0.5:
        score += 2
    elif ratio_buy_days <= (1 - STRONG_DISTRIB_THRESHOLD):
        score -= 3

    if divergence == "Yes":
        score += 1

    if trend == "Uptrend":
        score += 1
    elif trend == "Downtrend":
        score -= 1

    # --- Interpretasi sinyal ---
    if score >= 4:
        sentiment = "Strong Accumulation (Buy on breakout / hold strength)"
    elif 2 <= score < 4:
        sentiment = "Moderate Accumulation (Hold / add on weakness)"
    elif -2 <= score < 2:
        sentiment = "Neutral / Wait and See"
    elif -4 <= score < -2:
        sentiment = "Moderate Distribution (Take profit or reduce position)"
    else:
        sentiment = "Strong Distribution (Sell / Avoid for now)"

    # --- Cut loss & fleksibilitas ---
    support_price = round(df['Close'].min(), 2)
    cut_loss_price = round(support_price * 0.985, 2)
    buy_signal = avg_foreign_buy if score > 1 and trend == "Uptrend" else None
    sell_signal = avg_foreign_sell if score < -1 else None

    # --- Output laporan Telegram ---
    report = (
        f"*{ticker}* — Asing {'Beli' if net_foreign>0 else 'Jual'} {up_days}/{PERIOD} hari "
        f"({'Accumulation' if net_foreign>0 else 'Distribution'})\n"
        f"Rata-rata harga {'beli' if net_foreign>0 else 'jual'} asing: Rp {avg_foreign_buy if net_foreign>0 else avg_foreign_sell:,.0f}\n"
        f"Harga terakhir: Rp {last_price:,.0f} ({price_change_pct:+.1f}%)\n"
        f"Volume harian: {volume_ratio}% dari rata-rata\n"
        f"Net Asing: Rp {net_foreign/1e6:,.0f} M | Ritel: Rp {net_retail/1e6:,.0f} M\n"
        f"Tren harga: *{trend}* | Divergensi asing-ritel: *{divergence}*\n\n"
        f"📊 *Interpretasi:* {sentiment}\n"
    )

    # --- Penjelasan divergensi ---
    if divergence == "Yes":
        report += "🔄 *Divergensi terdeteksi:* Arah asing dan ritel berlawanan — potensi reversal atau pergeseran tren.\n"
    else:
        report += "🔹 Tidak ada divergensi signifikan antara asing dan ritel.\n"

    # --- Tambahan rekomendasi ---
    if buy_signal:
        report += f"💰 Rekomendasi beli bertahap di area Rp {buy_signal:,.0f}\n"
    if sell_signal:
        report += f"🚨 Rekomendasi jual / kurangi di area Rp {sell_signal:,.0f}\n"

    report += f"🛑 Cut loss jika turun di bawah Rp {cut_loss_price:,.0f}\n"

    return report
