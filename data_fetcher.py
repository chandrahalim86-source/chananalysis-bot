import pandas as pd
import requests
import datetime
import random

# Simulasi: data gabungan RTI + Stockbit
# Kamu bisa ganti dengan real endpoint RTI atau source CSV API sesuai kebutuhan

def get_stock_list():
    """Ambil daftar saham aktif likuid (bisa diperluas dari API real)."""
    return ["TLKM", "BBCA", "BBRI", "BMRI", "ASII", "UNVR", "MDKA", "ADRO", "ICBP", "ANTM",
            "INDF", "BBNI", "ITMG", "TPIA", "AMMN", "MEDC", "PGAS", "SMGR", "KLBF", "BRIS"]


def get_combined_data(symbol, period):
    """Ambil data foreign buy/sell & harga"""
    try:
        days = pd.date_range(end=datetime.date.today(), periods=period)
        close_prices = [random.uniform(2000, 7000) for _ in range(period)]
        value = [random.uniform(8e9, 20e9) for _ in range(period)]
        net_foreign = [random.uniform(-100e6, 100e6) for _ in range(period)]

        df = pd.DataFrame({
            'date': days,
            'close': close_prices,
            'value': value,
            'net_foreign': net_foreign
        })
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()
