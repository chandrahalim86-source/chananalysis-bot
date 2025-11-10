import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_foreign_flow(data, period=15):
    results = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for symbol, df in data.items():
        df = df.tail(period)
        if len(df) < period:
            continue

        avg_foreign = df['foreign_net'].mean()
        net_foreign = df['foreign_net'].sum()
        net_retail = df['retail_net'].sum()
        last_price = df['close'].iloc[-1]
        avg_value = df['value'].mean()
        price_change = (last_price - df['close'].iloc[0]) / df['close'].iloc[0] * 100

        corr = df['foreign_net'].corr(df['retail_net'])
        divergensi = "Yes" if corr < -0.5 else "No"

        foreign_sell_days = (df['foreign_net'] < 0).sum()
        trend = "Uptrend" if price_change > 3 else ("Downtrend" if price_change < -3 else "Sideways")

        # ChanScore
        chscore = max(0, min(100, 50 + (corr * -50) + (price_change / 2)))

        # Generate kesimpulan otomatis
        if divergensi == "Yes" and net_foreign < 0 and trend == "Uptrend":
            kesimpulan = (
                "Asing distribusi tapi ada divergensi kuat dengan ritel — indikasi hidden accumulation. "
                "Selama tren naik bertahan, boleh hold / tambah saat melemah."
            )
        elif net_foreign > 0 and trend == "Uptrend":
            kesimpulan = (
                "Asing akumulasi konsisten di tengah tren naik — momentum positif masih berlanjut."
            )
        elif net_foreign < 0 and trend == "Downtrend":
            kesimpulan = (
                "Asing distribusi di tengah tren turun — potensi lanjut koreksi, pertimbangkan take profit."
            )
        elif divergensi == "Yes" and trend == "Downtrend":
            kesimpulan = (
                "Harga turun tapi ritel akumulasi — potensi early reversal bila tekanan jual asing melemah."
            )
        else:
            kesimpulan = (
                "Pergerakan netral, tunggu konfirmasi arah dari akumulasi asing berikutnya."
            )

        result = {
            "symbol": symbol,
            "foreign_sell_days": foreign_sell_days,
            "period": period,
            "avg_foreign": round(avg_foreign, 2),
            "last_price": int(last_price),
            "price_change": round(price_change, 2),
            "net_foreign": net_foreign,
            "net_retail": net_retail,
            "avg_value": avg_value,
            "corr": round(corr, 2) if not np.isnan(corr) else 0,
            "divergensi": divergensi,
            "trend": trend,
            "chscore": round(chscore, 1),
            "kesimpulan": kesimpulan,
            "timestamp": now
        }
        results.append(result)

    return sorted(results, key=lambda x: abs(x['net_foreign']), reverse=True)
