import requests
import pandas as pd
from datetime import datetime, timedelta

# =========================
# Data Fetcher for Smart Adaptive Pro
# =========================
# Source 1: RTI (foreign buy/sell, daily)
# Source 2: Stockbit (price validation / fallback)

def fetch_rti_data(symbol: str, days: int = 15):
    """
    Mengambil data foreign buy/sell dan harga harian dari RTI.
    """
    try:
        url = f"https://www.rti.co.id/stock/api/chart/{symbol}/daily"
        r = requests.get(url, timeout=10)
        data = r.json()
        df = pd.DataFrame(data['data'])

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=True)
        df = df.tail(days)

        df['foreign_buy'] = df['foreignbuy'].astype(float)
        df['foreign_sell'] = df['foreignsell'].astype(float)
        df['close'] = df['close'].astype(float)
        df['value'] = df['value'].astype(float)

        df['net_foreign'] = df['foreign_buy'] - df['foreign_sell']
        return df[['date', 'close', 'foreign_buy', 'foreign_sell', 'net_foreign', 'value']]
    except Exception as e:
        print(f"[RTI] Error fetch {symbol}: {e}")
        return pd.DataFrame()


def fetch_stockbit_price(symbol: str):
    """
    Validasi harga terakhir dari Stockbit.
    """
    try:
        url = f"https://stockbit.com/api/charting/price/{symbol}?range=1d"
        r = requests.get(url, timeout=8)
        data = r.json()
        last_price = float(data['data']['close'])
        return last_price
    except Exception:
        return None


def validate_price(df: pd.DataFrame, symbol: str):
    """
    Validasi harga dari RTI menggunakan fallback Stockbit jika mismatch.
    """
    if df.empty:
        return df

    last_rti_price = df['close'].iloc[-1]
    stockbit_price = fetch_stockbit_price(symbol)

    if stockbit_price and abs(stockbit_price - last_rti_price) / last_rti_price > 0.03:
        print(f"[Validator] Adjusted {symbol} last price from RTI {last_rti_price} → Stockbit {stockbit_price}")
        df.at[df.index[-1], 'close'] = stockbit_price

    return df


def get_combined_data(symbol: str, days: int = 15):
    """
    Wrapper: Ambil data dari RTI + validasi harga Stockbit.
    """
    df = fetch_rti_data(symbol, days)
    df = validate_price(df, symbol)
    return df
