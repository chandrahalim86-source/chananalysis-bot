import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import get_combined_data

# =========================
# SMART ADAPTIVE PRO ANALYZER
# =========================

def compute_chanscore(df):
    """
    Hitung skor akumulasi asing dan strength tren harga.
    Range hasil: 0 – 100
    """
    if df.empty or len(df) < 5:
        return 0, "Insufficient Data"

    # Net asing kumulatif & slope harga
    net_foreign = df['net_foreign'].sum()
    price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100

    # Korelasi asing dengan harga (divergence check)
    corr = df['net_foreign'].corr(df['close'])
    if np.isnan(corr):
        corr = 0

    # Skor utama
    score = 50 + (net_foreign / abs(net_foreign) * min(abs(price_change), 10) * 2 if net_foreign != 0 else 0)
    score += corr * 20

    # Boundaries
    score = max(0, min(100, round(score, 1)))

    # Klasifikasi
    if score >= 70:
        phase = "Strong Accumulation"
    elif 55 <= score < 70:
        phase = "Moderate Accumulation"
    elif 45 <= score < 55:
        phase = "Neutral"
    elif 30 <= score < 45:
        phase = "Moderate Distribution"
    else:
        phase = "Strong Distribution"

    return score, phase


def interpret_signal(symbol, df, score, phase):
    """
    Hasilkan interpretasi & kesimpulan akhir berbasis kondisi asing & tren harga.
    """
    if df.empty:
        return f"{symbol}: Data tidak tersedia."

    # Info dasar
    last_price = df['close'].iloc[-1]
    last_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100 if len(df) >= 2 else 0
    avg_liquidity = df['value'].mean()
    net_10d = df['net_foreign'].tail(10).sum()
    net_retail = -net_10d  # Approximation, since total = foreign + retail ~ 0

    corr = df['net_foreign'].corr(df['close'])
    divergence = "Yes" if abs(corr) < 0.3 else "No"

    # Interpretasi tambahan (otomatis)
    kesimpulan = ""
    if "Accumulation" in phase:
        if last_change > 0 and corr > 0:
            kesimpulan = (
                "📈 Asing masih akumulasi konsisten, tren naik sehat. "
                "Hold / tambah saat koreksi ringan. Hindari jual terlalu cepat."
            )
        else:
            kesimpulan = (
                "📈 Asing akumulasi namun harga belum menguat. Sinyal potensi breakout, pantau volume."
            )
    elif "Distribution" in phase:
        if corr < 0:
            kesimpulan = (
                "⚠️ Asing mulai distribusi dan harga melemah. "
                "Jika tren turun berlanjut, pertimbangkan take profit / kurangi posisi."
            )
        else:
            kesimpulan = (
                "⚠️ Asing jual ringan namun harga stabil. Waspadai potensi distribusi lebih besar."
            )
    else:
        kesimpulan = (
            "⏸️ Sinyal netral, tunggu konfirmasi arah berikutnya sebelum ambil keputusan."
        )

    # Fleksibilitas jual: jangan terlalu cepat jika asing masih akumulasi
    if "Distribution" in phase and corr > -0.5:
        kesimpulan += "\n💡 Catatan: Distribusi belum kuat, tunggu konfirmasi lanjut sebelum jual penuh."

    # Format laporan
    report = f"""*{symbol}* — Asing {phase}

Rata-rata beli/jual asing: Rp {df['close'].mean():,.0f}
Harga terakhir: Rp {last_price:,.0f} ({last_change:.1f}%)
Net Asing (10d): Rp {net_10d:,.0f} | Ritel: Rp {net_retail:,.0f}
Likuiditas avg: Rp {avg_liquidity:,.0f}
ChanScore: {score} → {phase}
📊 Divergensi: {divergence} (corr={corr:.2f})
🔹 Kesimpulan: {kesimpulan}
"""
    return report


def analyze_top_stocks(symbols, period=15, min_liquidity=10_000_000_000, top_n=20):
    """
    Analisa seluruh saham, pilih yang paling akumulatif & likuid.
    """
    results = []

    for symbol in symbols:
        df = get_combined_data(symbol, period)
        if df.empty:
            continue

        avg_liq = df['value'].mean()
        if avg_liq < min_liquidity:
            continue

        score, phase = compute_chanscore(df)
        results.append({
            'symbol': symbol,
            'score': score,
            'phase': phase,
            'df': df
        })

    # Urutkan dari akumulasi terbesar
    ranked = sorted(results, key=lambda x: x['score'], reverse=True)[:top_n]

    # Format teks laporan untuk Telegram
    text_blocks = []
    for item in ranked:
        section = interpret_signal(item['symbol'], item['df'], item['score'], item['phase'])
        text_blocks.append(section)

    final_report = "\n\n" + ("—" * 30 + "\n\n").join(text_blocks)
    return final_report
