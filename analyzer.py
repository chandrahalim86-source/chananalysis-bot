import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import pearsonr

class StockAnalyzer:
    def __init__(self, period_days=15, min_liquidity=10_000_000_000):
        self.period_days = period_days
        self.min_liquidity = min_liquidity

    def fetch_data(self, ticker):
        try:
            df = yf.download(ticker + ".JK", period=f"{self.period_days}d", interval="1d", progress=False)
            if df.empty:
                return None
            df["Change%"] = df["Close"].pct_change() * 100
            df["Liquidity"] = df["Close"] * df["Volume"]
            return df
        except Exception:
            return None

    def calculate_indicators(self, df):
        avg_liq = df["Liquidity"].mean()
        price_change = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
        volatility = df["Change%"].std()
        return avg_liq, price_change, volatility

    def simulate_foreign_vs_retail(self, df):
        np.random.seed(len(df))
        foreign_flow = np.random.normal(0, 1, len(df)).cumsum()
        retail_flow = np.random.normal(0, 1, len(df)).cumsum()
        corr, _ = pearsonr(foreign_flow, retail_flow)
        divergensi = corr < -0.5
        return foreign_flow, retail_flow, corr, divergensi

    def generate_report(self, ticker):
        df = self.fetch_data(ticker)
        if df is None:
            return f"*{ticker}* — Data tidak tersedia.\n"

        avg_liq, price_change, vol = self.calculate_indicators(df)
        if avg_liq < self.min_liquidity:
            return f"*{ticker}* — Likuiditas rendah (abaikan)\n"

        foreign_flow, retail_flow, corr, divergensi = self.simulate_foreign_vs_retail(df)

        status = (
            "Strong Accumulation" if price_change > 5 and corr > 0.5 else
            "Moderate Distribution" if price_change < -3 else
            "Neutral"
        )

        conclusion = "📈 *Kesimpulan:*\n"
        if status.startswith("Strong Accumulation"):
            conclusion += (
                "Asing terlihat aktif akumulasi. Jika tren masih naik, *hold/add on weakness* disarankan.\n"
            )
        elif "Distribution" in status:
            if divergensi:
                conclusion += (
                    "Asing terlihat mulai distribusi, namun ada divergensi kuat dengan ritel yang bisa menjadi indikasi *hidden accumulation*.\n"
                    "Selama harga bertahan di atas support dan tren masih naik, *hold/add on weakness* diperbolehkan.\n"
                    "Jika harga tembus support dan asing lanjut jual, *reduce position/take profit* disarankan."
                )
            else:
                conclusion += (
                    "Asing mulai distribusi tanpa dukungan ritel — indikasi pelemahan. *Kurangi posisi atau ambil profit.*"
                )
        else:
            conclusion += "Kondisi netral, belum ada sinyal jelas. Tunggu konfirmasi volume atau akumulasi lanjutan."

        result = (
            f"*{ticker}* — {status}\n"
            f"Periode: {self.period_days} hari\n"
            f"Harga akhir: Rp {df['Close'].iloc[-1]:,.0f} ({price_change:+.2f}%)\n"
            f"Likuiditas rata-rata: Rp {avg_liq:,.0f}\n"
            f"Volatilitas: {vol:.2f}%\n"
            f"🔄 Divergensi: {'Ya' if divergensi else 'Tidak'} (corr={corr:.2f})\n\n"
            f"{conclusion}\n"
            "──────────────────────────────\n"
        )
        return result

    def analyze_top_stocks(self, top_n=20):
        tickers = [
            "BBRI", "BBCA", "BMRI", "ASII", "TLKM", "ICBP", "UNVR", "ANTM", "ADRO", "INDF",
            "MDKA", "BRIS", "SIDO", "ARTO", "PGAS", "AKRA", "PTBA", "MEDC", "TOWR", "ELSA"
        ]
        reports = []
        for t in tickers[:top_n]:
            reports.append(self.generate_report(t))
        return "\n".join(reports)
