# data_fetcher.py
import os
import requests
import pandas as pd

RTI_API_BASE = os.getenv("RTI_API_BASE", "https://rtiapi.rti.co.id")
RTI_EMAIL = os.getenv("RTI_EMAIL")
RTI_PASSWORD = os.getenv("RTI_PASSWORD")

def fetch_rti_daily_flow(symbol, days=15):
    try:
        url = f"{RTI_API_BASE}/api/StockDetail/{symbol}/ForeignFlow"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        js = resp.json()
        rows = []
        for item in js.get("data", [])[-days:]:
            rows.append({
                "date": pd.to_datetime(item.get("Date")),
                "close": float(item.get("Close", 0) or 0),
                "volume": float(item.get("Volume", 0) or 0),
                "foreign_buy": float(item.get("ForeignBuy", 0) or 0),
                "foreign_sell": float(item.get("ForeignSell", 0) or 0),
            })
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows).sort_values("date")
        return df.tail(days).reset_index(drop=True)
    except Exception as e:
        print(f"[WARN] fetch_rti_daily_flow {symbol} failed: {e}")
        return pd.DataFrame()

def fetch_stockbit_daily(symbol, days=15):
    try:
        url = f"https://stockbit.com/api/chart/{symbol}/historical?range={days}d"
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        js = resp.json()
        rows = []
        for item in js.get("data", []):
            t = item.get("t")
            if t is None:
                continue
            date = pd.to_datetime(int(t), unit='s')
            rows.append({
                "date": date,
                "close": float(item.get("c") or 0),
                "volume": float(item.get("v") or 0),
                "foreign_buy": 0.0,
                "foreign_sell": 0.0
            })
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows).sort_values("date")
        return df.tail(days).reset_index(drop=True)
    except Exception as e:
        print(f"[WARN] fetch_stockbit_daily {symbol} failed: {e}")
        return pd.DataFrame()

def get_timewindow_data(symbol, days=15):
    df = fetch_rti_daily_flow(symbol, days=days)
    if not df.empty and len(df) >= max(5, days//2):
        return df
    df2 = fetch_stockbit_daily(symbol, days=days)
    return df2

def fetch_top_foreign_symbols(top_n=20):
    try:
        url = f"{RTI_API_BASE}/api/Market/TopForeignFlow"
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        js = resp.json()
        symbols = [x.get("Code") for x in js.get("data", [])][:top_n]
        symbols = [s for s in symbols if s]
        if symbols:
            return symbols
    except Exception as e:
        print(f"[WARN] fetch_top_foreign_symbols failed: {e}")

    fallback = ["TLKM","BBCA","BBRI","BMRI","ASII","UNVR","MDKA","ADRO","ICBP","ANTM",
                "INDF","BBNI","ITMG","TPIA","AMMN","MEDC","PGAS","SMGR","KLBF","BRIS"]
    return fallback[:top_n]
