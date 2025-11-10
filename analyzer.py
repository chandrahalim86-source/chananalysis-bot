import pandas as pd
import numpy as np
from datetime import datetime

def analyze_top_stocks(days=15, top_n=20, min_liquidity=10_000_000_000):
    # === Dummy data generator ===
    # Gantilah bagian ini dengan koneksi data real kamu nanti
    stocks = ["TLKM", "BBCA", "BMRI", "ASII", "BBRI", "BBNI", "ADRO", "MDKA", "UNVR", "ICBP",
              "INDF", "ANTM", "PGAS", "SMGR", "AKRA", "CPIN", "MYOR", "TOWR", "ESSA", "BRIS"]
    np.random.seed(42)
    
    results = []
    for stock in stocks[:top_n]:
        net_foreign = np.random.randint(-200_000_000, 200_000_000)
        retail_flow = -net_foreign + np.random.randint(-20_000_000, 20_000_000)
        last_price = np.random.randint(1000, 7000)
        avg_price = last_price + np.random.randint(-200, 200)
        liquidity = np.random.randint(min_liquidity, min_liquidity * 2)
        ch_score = np.random.uniform(20, 90)
        corr = np.random.uniform(-0.9, 0.9)
        signal = "Strong Accumulation" if net_foreign > 50_000_000 else (
                 "Strong Distribution" if net_foreign < -50_000_000 else "Neutral")

        # Dynamic interpretation
        conclusion = []
        if net_foreign > 50_000_000:
            conclusion.append("Asing terlihat melakukan akumulasi.")
            if corr < -0.6:
                conclusion.append("Divergensi kuat dengan ritel — indikasi *hidden accumulation*.")
        elif net_foreign < -50_000_000:
            conclusion.append("Asing mulai distribusi.")
            if corr < -0.6:
                conclusion.append("Divergensi kuat dengan ritel — bisa jadi *early reversal signal*.")
        else:
            conclusion.append("Aksi asing relatif netral terhadap ritel.")

        suggestion = (
            f"Selama harga bertahan di atas Rp {last_price*0.97:,.0f} dan tren naik, "
            f"hold atau tambah saat koreksi diperbolehkan."
            if net_foreign > 0
            else f"Jika harga tembus Rp {last_price*0.97:,.0f}, pertimbangkan take profit atau reduce position."
        )

        summary = (
            f"*{stock}* — {signal}\n"
            f"Rata-rata beli/jual asing: Rp {avg_price:,}\n"
            f"Harga terakhir: Rp {last_price:,}\n"
            f"Net Asing (10d): Rp {net_foreign:,} | Ritel: Rp {retail_flow:,}\n"
            f"Likuiditas avg: Rp {liquidity:,}\n"
            f"ChanScore: {ch_score:.1f}/100\n"
            f"🔄 Korelasi asing-ritel: {corr:.2f}\n\n"
            f"📈 Kesimpulan:\n- {' '.join(conclusion)}\n- {suggestion}\n\n"
        )
        results.append(summary)

    report = (
        f"*Laporan Akumulasi Asing ({days} Hari)*\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        + "\n".join(results)
    )
    return report
