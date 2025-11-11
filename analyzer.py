import numpy as np
import pandas as pd
from datetime import datetime
import random

# Simulasi fetch data dari data_fetcher (bisa diintegrasikan dengan RTI / Stockbit API)
from data_fetcher import fetch_stock_data

def format_currency(value):
    if abs(value) >= 1_000_000_000:
        return f"Rp {value/1_000_000_000:.1f} M"
    elif abs(value) >= 1_000_000:
        return f"Rp {value/1_000_000:.1f} Jt"
    else:
        return f"Rp {value:,.0f}"

def analyze_foreign_flow(period=15, min_liquidity=10_000_000_000, top_n=20):
    """
    Analisis akumulasi asing berdasarkan data 15 hari terakhir (default).
    """
    stocks = fetch_stock_data()

    report_lines = []
    report_lines.append(f"*Laporan Akumulasi Asing ({period} Hari)*\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    for s in stocks:
        # Simulasi data real — nanti diganti fetch dari RTI
        price_now = random.randint(1000, 6000)
        avg_price = price_now + random.randint(-200, 200)
        net_foreign = random.randint(-200_000_000, 300_000_000)
        net_retail = -net_foreign * 0.9
        liquidity = random.randint(10_000_000_000, 60_000_000_000)
        corr = random.uniform(-1, 1)

        if liquidity < min_liquidity:
            continue

        score = (
            (net_foreign / 100_000_000) +
            (liquidity / 1_000_000_000) * 0.3 +
            (1 - abs(corr)) * 20
        )

        results.append({
            "code": s,
            "price_now": price_now,
            "avg_price": avg_price,
            "net_foreign": net_foreign,
            "net_retail": net_retail,
            "liquidity": liquidity,
            "corr": corr,
            "score": score
        })

    df = pd.DataFrame(results)
    df = df.sort_values("score", ascending=False).head(top_n)

    for _, row in df.iterrows():
        trend = "Uptrend" if row["price_now"] > row["avg_price"] else "Downtrend"
        signal = "Accumulation" if row["net_foreign"] > 0 else "Distribution"

        divergence = "Yes" if abs(row["corr"]) < 0.5 else "No"
        diver_text = (
            f"🔄 Divergensi: {divergence} (corr={row['corr']:.2f}) — "
            + ("asing dan ritel bergerak berlawanan — *sinyal early reversal / hidden accumulation*."
               if divergence == "Yes" else "pergerakan selaras antara asing dan ritel.")
        )

        if signal == "Accumulation":
            rec = "✅ Potensi akumulasi asing — perhatikan momentum entry saat volume meningkat."
        elif trend == "Uptrend" and signal == "Distribution":
            rec = "⚠️ Asing jual, tapi tren masih naik — hold atau gunakan trailing stop."
        else:
            rec = "🛑 Asing distribusi dan tren melemah — hindari entry baru."

        kesimpulan = (
            f"📈 *Kesimpulan:*\n"
            f"Asing {signal.lower()} selama {period} hari terakhir. "
            f"{'Tren masih naik' if trend == 'Uptrend' else 'Tren melemah'}. "
            f"{'Perhatikan potensi rebound' if divergence == 'Yes' else ''}\n"
            f"{rec}"
        )

        text = (
            f"\n*{row['code']}* — Asing {signal} ({trend})\n"
            f"Rata-rata harga asing: {format_currency(row['avg_price'])}\n"
            f"Harga terakhir: {format_currency(row['price_now'])}\n"
            f"Net Asing ({period}d): {format_currency(row['net_foreign'])} | Ritel: {format_currency(row['net_retail'])}\n"
            f"Likuiditas rata-rata: {format_currency(row['liquidity'])}\n"
            f"ChanScore: {row['score']:.1f}/100 — {signal}\n"
            f"{diver_text}\n"
            f"{kesimpulan}"
        )

        report_lines.append(text)
        report_lines.append("\n──────────────────────────────")

    return "\n".join(report_lines)
