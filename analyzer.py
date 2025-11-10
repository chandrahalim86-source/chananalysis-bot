import pandas as pd
import numpy as np
from datetime import datetime

def analyze_foreign_flow(data: dict, period: int = 15):
    """
    Menganalisa akumulasi dan distribusi asing dari data saham.
    Data: dict {symbol: DataFrame[close, foreign_net, retail_net, value]}
    """
    results = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for symbol, df in data.items():
        df = df.tail(period)
        if len(df) < period:
            continue

        # --- Perhitungan dasar ---
        net_foreign = df['foreign_net'].sum()
        net_retail = df['retail_net'].sum()
        avg_foreign = df['foreign_net'].mean()
        avg_value = df['value'].mean()
        last_price = df['close'].iloc[-1]
        first_price = df['close'].iloc[0]
        price_change = (last_price - first_price) / first_price * 100
        foreign_sell_days = (df['foreign_net'] < 0).sum()

        # --- Korelasi & Divergensi ---
        corr = df['foreign_net'].corr(df['retail_net'])
        divergensi = "Yes" if corr is not np.nan and corr < -0.5 else "No"

        # --- Penentuan tren harga ---
        if price_change > 5:
            trend = "Uptrend"
        elif price_change < -5:
            trend = "Downtrend"
        else:
            trend = "Sideways"

        # --- ChanScore (stabilitas akumulasi) ---
        chscore = 50
        chscore += (price_change / 2)
        chscore += (-corr * 25)
        chscore += (10 if net_foreign > 0 else -10)
        chscore = max(0, min(100, round(chscore, 1)))

        # --- Kesimpulan Otomatis ---
        if net_foreign > 0 and trend == "Uptrend":
            kesimpulan = (
                "Asing akumulasi kuat sejalan tren naik — momentum masih positif. "
                "Hold atau tambah posisi saat melemah."
            )
        elif net_foreign > 0 and trend == "Downtrend":
            kesimpulan = (
                "Asing mulai akumulasi meski tren turun — sinyal awal potensi reversal. "
                "Pantau volume dan harga penutupan 2-3 hari ke depan."
            )
        elif net_foreign < 0 and trend == "Downtrend":
            kesimpulan = (
                "Asing distribusi di tengah tren turun — potensi lanjut koreksi, "
                "take profit atau kurangi posisi disarankan."
            )
        elif net_foreign < 0 and trend == "Uptrend":
            if divergensi == "Yes":
                kesimpulan = (
                    "Asing distribusi namun ada divergensi kuat dengan ritel — "
                    "indikasi hidden accumulation. "
                    "Selama harga bertahan, hold atau tambah saat koreksi ringan."
                )
            else:
                kesimpulan = (
                    "Asing distribusi di tengah tren naik — potensi pelemahan jangka pendek, "
                    "gunakan trailing stop."
                )
        else:
            kesimpulan = (
                "Pergerakan netral, belum ada sinyal dominan dari asing atau ritel."
            )

        result = {
            "symbol": symbol,
            "period": period,
            "foreign_sell_days": foreign_sell_days,
            "avg_foreign": round(avg_foreign, 2),
            "net_foreign": round(net_foreign, 2),
            "net_retail": round(net_retail, 2),
            "avg_value": round(avg_value, 2),
            "price_change": round(price_change, 2),
            "last_price": int(last_price),
            "corr": round(corr, 2) if not np.isnan(corr) else 0,
            "divergensi": divergensi,
            "trend": trend,
            "chscore": chscore,
            "kesimpulan": kesimpulan,
            "timestamp": now
        }

        results.append(result)

    # Urutkan berdasarkan nilai absolut net asing (paling aktif)
    results = sorted(results, key=lambda x: abs(x['net_foreign']), reverse=True)
    return results
