# analyzer.py
import os
import math
import numpy as np
import pandas as pd
from datetime import datetime
from data_fetcher import get_timewindow_data, fetch_top_foreign_symbols

ANALYSIS_PERIOD = int(os.getenv("ANALYSIS_PERIOD", "15"))
TOP_N = int(os.getenv("TOP_N", "20"))
MIN_LIQUIDITY_VALUE = float(os.getenv("MIN_LIQUIDITY_VALUE", "10000000000"))

def compute_metrics(df):
    if df.empty:
        return None
    df = df.copy()
    df['net_buy'] = df['foreign_buy'] - df['foreign_sell']
    total_net = df['net_buy'].sum()
    total_foreign_buy = df['foreign_buy'].sum()
    if total_foreign_buy > 0:
        avg_price_foreign = (df['close'] * df['foreign_buy']).sum() / total_foreign_buy
    else:
        avg_price_foreign = df['close'].mean()
    df['daily_value'] = df['close'] * df['volume']
    avg_daily_value = df['daily_value'].mean()
    streak = int((df['net_buy'] > 0).sum())
    try:
        x = np.arange(len(df))
        y = df['close'].values
        if len(x) >= 2:
            m, b = np.polyfit(x, y, 1)
            slope = m / (y.mean() if y.mean() != 0 else 1)
        else:
            slope = 0.0
    except Exception:
        slope = 0.0
    last_price = float(df['close'].iloc[-1])
    prev_price = float(df['close'].iloc[-2]) if len(df) >= 2 else last_price
    pct_change = (last_price - prev_price) / prev_price * 100 if prev_price != 0 else 0.0
    metrics = {
        "total_net": float(total_net),
        "total_foreign_buy": float(total_foreign_buy),
        "avg_price_foreign": round(float(avg_price_foreign), 2),
        "avg_daily_value": float(avg_daily_value),
        "streak": streak,
        "slope": float(slope),
        "last_price": last_price,
        "pct_change": round(pct_change, 2),
        "days": len(df),
        "df": df
    }
    return metrics

def chan_score(metrics, period=ANALYSIS_PERIOD):
    accum_score = min(metrics["streak"], period) / period * 40
    slope = metrics.get("slope", 0.0)
    slope_norm = max(min(slope * 100, 1.0), -1.0)
    momentum_score = max(0.0, slope_norm) * 30
    ldv = metrics.get("avg_daily_value", 0.0)
    if ldv <= 0:
        liquidity_score = 0.0
    else:
        baseline = MIN_LIQUIDITY_VALUE
        ratio = min(ldv / baseline, 10.0)
        liquidity_score = (math.log1p(ratio) / math.log1p(10.0)) * 20
    base = accum_score + momentum_score + liquidity_score
    base = max(0.0, min(base, 90.0))
    return round(base, 1)

def detect_divergence(metrics):
    df = metrics["df"]
    if df.empty or len(df) < 5:
        return {"is_divergent": False, "corr": None}
    price_change = df['close'].pct_change().fillna(0)
    net_buy = df['net_buy'].fillna(0)
    try:
        corr = price_change.corr(net_buy)
        is_div = corr is not None and corr < -0.4
        return {"is_divergent": bool(is_div), "corr": round(float(corr), 2) if corr is not None else None}
    except Exception:
        return {"is_divergent": False, "corr": None}

def recommend_levels(metrics):
    last = metrics["last_price"]
    avg_buy = metrics["avg_price_foreign"]
    buy_low = round(min(avg_buy * 0.98, last * 0.98), 2)
    buy_high = round(max(avg_buy * 1.02, last * 1.02), 2)
    if metrics["total_net"] < 0:
        cut_loss_pct = 0.03
    else:
        cut_loss_pct = 0.06
    cut_loss_price = round(last * (1 - cut_loss_pct), 2)
    return {"buy_low": buy_low, "buy_high": buy_high, "cut_loss": cut_loss_price}

def interpret(metrics, chan_score_val, divergence):
    tnet = metrics["total_net"]
    streak = metrics["streak"]
    slope = metrics["slope"]
    last = metrics["last_price"]
    if chan_score_val >= 75 and tnet > 0:
        rec = "Strong Accumulation (Buy / Add on weakness)"
    elif 50 <= chan_score_val < 75 and tnet > 0:
        rec = "Moderate Accumulation (Hold / Add on weakness)"
    elif tnet < 0 and chan_score_val < 50:
        rec = "Distribution (Reduce position / Take profit)"
    else:
        rec = "Neutral (Watch / Wait for confirmation)"
    if slope > 0.0 and tnet > 0:
        rec_detail = "Tren naik terkonfirmasi; fleksibel: jangan cepat jual, gunakan add-on on weakness / trailing stop."
    elif tnet < 0 and slope <= 0.0:
        rec_detail = "Asing mulai jual dan tren melemah; kurangi posisi."
    else:
        rec_detail = "Monitor pergerakan harga dan akumulasi asing."
    div_text = ""
    if divergence["is_divergent"]:
        div_text = (f"🔄 Divergensi terdeteksi (corr={divergence.get('corr')}). "
                    "Asing dan retail bergerak berlawanan — indikasi early reversal / hidden accumulation.")
    else:
        div_text = "🔄 Divergensi: None or weak."
    return rec, rec_detail, div_text

def analyze_foreign_flow(analysis_period=ANALYSIS_PERIOD, top_n=TOP_N, min_liq=MIN_LIQUIDITY_VALUE):
    results = []
    symbols = fetch_top_foreign_symbols(top_n)
    for sym in symbols:
        df = get_timewindow_data(sym, days=analysis_period)
        if df.empty or len(df) < max(5, analysis_period//3):
            continue
        metrics = compute_metrics(df)
        if metrics is None:
            continue
        if metrics["avg_daily_value"] < min_liq:
            continue
        base_score = chan_score(metrics, period=analysis_period)
        divergence = detect_divergence(metrics)
        div_bonus = 10.0 if divergence["is_divergent"] else 0.0
        final_score = min(100.0, round(base_score + div_bonus, 1))
        levels = recommend_levels(metrics)
        rec, rec_detail, div_text = interpret(metrics, final_score, divergence)
        results.append({
            "symbol": sym,
            "metrics": metrics,
            "chan_score": final_score,
            "base_score": base_score,
            "divergence": divergence,
            "recommendation": rec,
            "rec_detail": rec_detail,
            "levels": levels
        })
    results_sorted = sorted(results, key=lambda x: x["metrics"]["total_net"], reverse=True)[:top_n]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [f"*Laporan Akumulasi Asing ({analysis_period} Hari)*\nGenerated: {now}\n"]
    for r in results_sorted:
        m = r["metrics"]
        total_net_fmt = f"Rp {int(m['total_net']):,}" if abs(m['total_net']) >= 1000 else str(m['total_net'])
        total_buy_fmt = f"Rp {int(r['metrics']['total_foreign_buy']):,}"
        avg_liq_fmt = f"Rp {int(m['avg_daily_value']):,}"
        last_fmt = f"Rp {m['last_price']:,}"
        retail_est = -m['total_net']
        retail_fmt = f"Rp {int(retail_est):,}"
        divergence_corr = r['divergence'].get('corr') if r['divergence'] else None
        lines.append(
            f"*{r['symbol']}* — {'Asing Beli' if m['total_net']>0 else 'Asing Jual'} "
            f"{r['streak']}/{analysis_period} hari ({r['recommendation']})\n"
            f"Rata-rata beli asing: Rp {r['metrics']['avg_price_foreign']:,}\n"
            f"Harga terakhir: {last_fmt} ({r['metrics']['pct_change']}%)\n"
            f"Net Asing ({analysis_period}d): {total_net_fmt} | Ritel: {retail_fmt}\n"
            f"Likuiditas avg: {avg_liq_fmt}\n"
            f"ChanScore: {r['chan_score']}/100 → {r['recommendation']}\n"
            f"🔄 Divergensi: {divergence_corr or '-'}\n"
            f"🛑 Cut loss (saran): Rp {r['levels']['cut_loss']:,}\n"
            f"📈 Kesimpulan: {r['rec_detail']}\n"
            "—\n"
        )
    report_text = "\n".join(lines) if len(lines) > 1 else "Tidak ada saham yang memenuhi kriteria hari ini."
    return report_text, results_sorted
