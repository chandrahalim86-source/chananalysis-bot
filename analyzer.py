# analyzer.py
"""
Analyzer module - Smart Adaptive Pro
- Ambil data RTI (login + scrape) selama PERIOD (default 10 trading days)
- Fallback ke Stockbit publik untuk price/volume jika perlu
- Hitung metrik per simbol: foreign buy/sell, net, streak, weighted avg price
- Hitung ChanScore (dengan bobot yang disepakati)
- Deteksi divergensi asing vs ritel (jika data ritel tersedia)
- Hasil: teks laporan siap dikirim ke Telegram
"""

import os
import time
import math
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# -------------------------
# Config (env)
# -------------------------
RTI_EMAIL = os.getenv("RTI_EMAIL")
RTI_PASSWORD = os.getenv("RTI_PASSWORD")
RTI_LOGIN_URL = os.getenv("RTI_LOGIN_URL", "https://access.rti.co.id/auth/login")
RTI_FOREIGN_URL = os.getenv("RTI_FOREIGN_URL", "https://rti.co.id/stock/foreign")  # may change

STOCKBIT_SYMBOL_URL = os.getenv("STOCKBIT_SYMBOL_URL", "https://stockbit.com/symbols/{}")

PERIOD = int(os.getenv("ANALYSIS_PERIOD", "10"))          # default 10 trading days
MIN_LIQUIDITY_VALUE = int(os.getenv("MIN_LIQUIDITY_VALUE", str(10_000_000_000)))  # 10B IDR default
TOP_N = int(os.getenv("TOP_N", "10"))

# -------------------------
# Helpers
# -------------------------
def safe_float(x, default=np.nan):
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip().replace(",", "").replace("IDR", "").replace("Rp", "")
        # remove non-numeric characters except dot and minus
        import re
        s = re.sub(r"[^\d\.\-]", "", s)
        return float(s) if s != "" else default
    except Exception:
        return default

def human_idr(x):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return "-"
        return f"Rp {int(round(x)):,}"
    except Exception:
        return "-"

# -------------------------
# RTI scraping (login + per-date table)
# -------------------------
def fetch_rti_table_for_date(session, date_str):
    """
    Scrape RTI foreign table for a given date string 'YYYY-MM-DD'.
    Returns list of dict rows with keys: symbol, foreign_buy, foreign_sell, price, maybe retail if present.
    NOTE: RTI layout changes — may need update.
    """
    try:
        url = f"{RTI_FOREIGN_URL}?date={date_str}"
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return []
        rows = []
        trs = table.select("tr")[1:]  # skip header
        for tr in trs:
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            # Heuristic: adapt if RTI columns differ
            if len(tds) < 5:
                continue
            symbol = tds[0]
            # heuristics for columns - may require adjustments
            fb = safe_float(tds[2])
            fs = safe_float(tds[3])
            price = safe_float(tds[4])
            # optional retail columns if present after
            retail_val = None
            if len(tds) >= 7:
                # try to find retail net or retail buy
                retail_val = safe_float(tds[6])
            rows.append({
                "symbol": symbol,
                "foreign_buy": fb if not math.isnan(fb) else 0.0,
                "foreign_sell": fs if not math.isnan(fs) else 0.0,
                "price": price if not math.isnan(price) else None,
                "retail_net": retail_val
            })
        return rows
    except Exception:
        return []

def fetch_rti_data(days=PERIOD):
    """
    Login (if credentials provided) and fetch last `days` trading days of RTI foreign data.
    Returns DataFrame with columns: date,symbol,foreign_buy,foreign_sell,price,retail_net (optional)
    """
    data = []
    if not RTI_EMAIL or not RTI_PASSWORD:
        # No credentials -> return empty DataFrame so caller can fallback
        return pd.DataFrame(columns=["date","symbol","foreign_buy","foreign_sell","price","retail_net"])

    session = requests.Session()
    try:
        payload = {"email": RTI_EMAIL, "password": RTI_PASSWORD}
        session.post(RTI_LOGIN_URL, data=payload, timeout=12)
        # ignore strict status code; some RTI endpoints still require tokens
    except Exception:
        return pd.DataFrame(columns=["date","symbol","foreign_buy","foreign_sell","price","retail_net"])

    fetched = 0
    d = datetime.now()
    attempts = 0
    max_attempts = days * 4
    while fetched < days and attempts < max_attempts:
        date_str = d.strftime("%Y-%m-%d")
        rows = fetch_rti_table_for_date(session, date_str)
        if rows:
            for r in rows:
                r["date"] = date_str
                data.append(r)
            fetched += 1
        d = d - timedelta(days=1)
        attempts += 1
        time.sleep(0.15)
    if not data:
        return pd.DataFrame(columns=["date","symbol","foreign_buy","foreign_sell","price","retail_net"])
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["foreign_buy"] = df["foreign_buy"].astype(float)
    df["foreign_sell"] = df["foreign_sell"].astype(float)
    df["price"] = df["price"].astype(float, errors="ignore")
    return df

# -------------------------
# Stockbit public fallback
# -------------------------
def fetch_stockbit_public(symbol):
    """
    Try to fetch last price and volume from Stockbit public symbol page (heuristic).
    Returns dict {'last_price': float or None, 'volume': int or None}
    """
    try:
        url = STOCKBIT_SYMBOL_URL.format(symbol.lower())
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {"last_price": None, "volume": None}
        soup = BeautifulSoup(r.text, "html.parser")
        # heuristics for price
        price_tag = soup.select_one(".price") or soup.select_one(".ticker-last-price")
        vol_tag = soup.find(string=lambda t: t and "Volume" in t) or soup.select_one(".volume")
        last_price = safe_float(price_tag.get_text() if price_tag else None)
        volume = None
        if vol_tag:
            # try extract number
            import re
            txt = vol_tag.get_text() if hasattr(vol_tag, "get_text") else str(vol_tag)
            m = re.search(r"(\d[\d,\.]*)", txt.replace(",", ""))
            if m:
                try:
                    volume = int(m.group(1).replace(".", "").replace(",", ""))
                except:
                    volume = None
        return {"last_price": last_price, "volume": volume}
    except Exception:
        return {"last_price": None, "volume": None}

# -------------------------
# Metrics & scoring
# -------------------------
def calculate_metrics_for_symbol(df_sym):
    """
    df_sym: DataFrame rows for a symbol (date, foreign_buy, foreign_sell, price, retail_net optional)
    Returns dict metrics including net_foreign, streak (days foreign net > 0), weighted avg buy price, last price, pct change vs avg.
    """
    df_sym = df_sym.sort_values("date").tail(PERIOD).copy()
    if df_sym.empty:
        return None
    df_sym["net_buy"] = df_sym["foreign_buy"] - df_sym["foreign_sell"]

    foreign_buy_total = df_sym["foreign_buy"].sum()
    foreign_sell_total = df_sym["foreign_sell"].sum()
    net_foreign = foreign_buy_total - foreign_sell_total
    up_days = int((df_sym["net_buy"] > 0).sum())
    down_days = int((df_sym["net_buy"] < 0).sum())
    streak = up_days

    # weighted avg price using foreign_buy as weight, fallback avg price
    try:
        weighted_avg_price = (df_sym["price"] * df_sym["foreign_buy"]).sum() / (df_sym["foreign_buy"].sum() + 1e-9)
    except Exception:
        weighted_avg_price = df_sym["price"].mean()

    last_price = df_sym["price"].iloc[-1] if "price" in df_sym.columns and not df_sym["price"].isna().all() else None
    avg_price = df_sym["price"].mean() if "price" in df_sym.columns else None
    pct_change = ((last_price - avg_price) / avg_price * 100) if (avg_price and last_price) else 0.0

    # retail net (sum) if present
    retail_net = df_sym["retail_net"].sum() if "retail_net" in df_sym.columns and not df_sym["retail_net"].isna().all() else None

    metrics = {
        "symbol": df_sym["symbol"].iloc[0],
        "foreign_buy_total": float(foreign_buy_total),
        "foreign_sell_total": float(foreign_sell_total),
        "net_foreign": float(net_foreign),
        "up_days": up_days,
        "down_days": down_days,
        "streak": streak,
        "weighted_avg_price": float(round(weighted_avg_price, 2)) if not math.isnan(weighted_avg_price) else None,
        "last_price": float(round(last_price, 2)) if last_price is not None and not math.isnan(last_price) else None,
        "avg_price": float(round(avg_price, 2)) if avg_price is not None and not math.isnan(avg_price) else None,
        "pct_change_vs_avg": float(round(pct_change, 2)),
        "days_counted": len(df_sym),
        "retail_net": float(retail_net) if retail_net is not None else None
    }
    return metrics

def chan_score_calc(metrics, liquidity_avg_value=None, total_turnover=None):
    """
    Compute ChanScore (0..100)
    Weights (final/proposed):
      - foreign streak normalized (45%)
      - net volume ratio normalized (25%)
      - price stability (15%)
      - liquidity score (10%)
      - (divergence adjustment applied later +/- 5)
    """
    streak = metrics.get("streak", 0)
    days = metrics.get("days_counted", PERIOD)
    foreign_net = metrics.get("net_foreign", 0)
    weighted_avg_price = metrics.get("weighted_avg_price") or metrics.get("avg_price") or 0
    last_price = metrics.get("last_price") or weighted_avg_price or 0

    foreign_streak_norm = min(1.0, streak / days)

    # net volume ratio normalization (heuristic): relative to turnover
    if total_turnover and total_turnover > 0:
        net_volume_ratio = abs(foreign_net) / total_turnover  # 0..inf
        net_volume_ratio_norm = max(0.0, min(1.0, net_volume_ratio * 10))  # scale factor heuristic
    else:
        net_volume_ratio_norm = 0.5 if abs(foreign_net) > 0 else 0.0

    # price stability metric: how close last price to weighted avg
    if weighted_avg_price and weighted_avg_price > 0:
        dev = abs(last_price - weighted_avg_price) / weighted_avg_price
        price_stability = max(0.0, 1 - min(dev, 0.5))
    else:
        price_stability = 0.5

    # liquidity score relative to MIN_LIQUIDITY_VALUE
    if liquidity_avg_value:
        liquidity_score = min(1.0, liquidity_avg_value / MIN_LIQUIDITY_VALUE)
    else:
        liquidity_score = 0.5

    base_score = (
        0.45 * foreign_streak_norm +
        0.25 * net_volume_ratio_norm +
        0.15 * price_stability +
        0.10 * liquidity_score
    ) * 100

    return round(base_score, 1)

# -------------------------
# Divergence detection
# -------------------------
def detect_divergence(df_sym):
    """
    If retail data present (Retail_Buy_Sell or retail_net), compute correlation between foreign net and retail net.
    Returns (flag(bool), corr(float or None), explanation)
    """
    if "net_buy" not in df_sym.columns or "retail_net" not in df_sym.columns:
        return False, None, "Data ritel tidak tersedia untuk deteksi divergensi."

    tmp = df_sym[["net_buy", "retail_net"]].dropna()
    if len(tmp) < 3:
        return False, None, "Data ritel/asing tidak cukup untuk korelasi."

    corr = tmp["net_buy"].corr(tmp["retail_net"])
    if pd.isna(corr):
        return False, None, "Korelasi tidak bisa dihitung."

    if corr < -0.65:
        expl = ("Divergensi kuat: asing dan ritel bergerak berlawanan — sinyal early reversal/hidden accumulation.")
        return True, round(corr, 2), expl
    elif corr < -0.4:
        expl = ("Divergensi sedang: ada kecenderungan berlawanan antara asing dan ritel.")
        return True, round(corr, 2), expl
    else:
        return False, round(corr, 2), "Tidak ada divergensi signifikan."

# -------------------------
# Report generation
# -------------------------
def generate_report(top_n=TOP_N, liquidity_filter=True, min_liquidity=MIN_LIQUIDITY_VALUE):
    """
    Master function returning text report.
    Steps:
      - fetch RTI data (PERIOD days)
      - aggregate per symbol
      - compute metrics, ChanScore, divergence, cutloss, recommendations
      - filter by liquidity
      - sort by score and return top_n results as markdown text
    """
    df = fetch_rti_data(days=PERIOD)
    if df.empty:
        return "❌ Gagal ambil data RTI atau RTI kosong. Pastikan RTI_EMAIL & RTI_PASSWORD benar, atau RTI layout belum berubah."

    symbols = sorted(df["symbol"].unique().tolist())
    results = []

    for sym in symbols:
        rows = df[df["symbol"] == sym].copy()
        if rows.empty:
            continue
        # ensure columns
        rows["net_buy"] = rows["foreign_buy"] - rows["foreign_sell"]
        metrics = calculate_metrics_for_symbol(rows)
        if not metrics:
            continue

        # stockbit fallback for liquidity/volume
        sb = fetch_stockbit_public(sym)
        liquidity_avg_value = None
        total_turnover = None
        if sb.get("last_price") and sb.get("volume"):
            liquidity_avg_value = sb["last_price"] * (sb["volume"] or 1)
            total_turnover = liquidity_avg_value * PERIOD

        # liquidity filter
        if liquidity_filter and (liquidity_avg_value is None or liquidity_avg_value < min_liquidity):
            continue

        # divergence detection (if retail exists)
        rows_for_div = rows.copy()
        if "retail_net" not in rows_for_div.columns:
            rows_for_div["retail_net"] = np.nan
        is_div, corr_val, div_exp = detect_divergence(rows_for_div)

        base_score = chan_score_calc(metrics, liquidity_avg_value=liquidity_avg_value, total_turnover=total_turnover)
        # divergensi modifier
        if is_div:
            if metrics["net_foreign"] > 0:
                base_score += 5
            else:
                base_score -= 5
        score = max(0.0, min(100.0, base_score))

        # compute recommended levels
        avg_buy_price = metrics.get("weighted_avg_price") or metrics.get("avg_price")
        last_price = metrics.get("last_price")
        support = avg_buy_price * 0.985 if avg_buy_price else (last_price * 0.98 if last_price else None)
        # cut loss lower than support but not too tight
        cut_loss = round((support or last_price or 0) * 0.985, 2) if (support or last_price) else None

        # recommended buy/sell zones:
        rec_buy = None
        rec_sell = None
        if score >= 85:
            label = "Strong Accumulation"
            advice = "Buy on breakout / Hold - aggressive"
            rec_buy = avg_buy_price or last_price
            rec_sell = last_price * 1.08 if last_price else None
        elif score >= 70:
            label = "Moderate Accumulation"
            advice = "Hold / Add on weakness (scale-in)"
            rec_buy = avg_buy_price * 0.99 if avg_buy_price else last_price
            rec_sell = last_price * 1.06 if last_price else None
        elif score >= 55:
            label = "Neutral / Wait"
            advice = "Wait confirmation (watch volume & foreign net)"
            rec_buy = None
            rec_sell = None
        elif score >= 40:
            label = "Moderate Distribution"
            advice = "Take profit / reduce position"
            rec_buy = None
            rec_sell = last_price * 0.995 if last_price else None
        else:
            label = "Strong Distribution"
            advice = "Sell / Avoid"
            rec_buy = None
            rec_sell = None

        # trend detection simple (flexible)
        trend = "Uptrend" if last_price and avg_buy_price and last_price > (avg_buy_price * 1.01) else "Check Trend"

        results.append({
            "symbol": sym,
            "score": round(score,1),
            "label": label,
            "advice": advice,
            "metrics": metrics,
            "liquidity_avg_value": liquidity_avg_value,
            "divergence": {"flag": is_div, "corr": corr_val, "explanation": div_exp},
            "cut_loss": cut_loss,
            "rec_buy": rec_buy,
            "rec_sell": rec_sell,
            "trend": trend
        })

    if not results:
        return "Tidak ada saham likuid yang memenuhi filter likuiditas pada periode ini."

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]

    # build markdown report
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"📊 *Laporan Akumulasi Asing ({PERIOD} Hari)*\nGenerated: {ts}\n\n"
    body_lines = []
    for r in results:
        m = r["metrics"]
        sym = r["symbol"]
        net_as = m["net_foreign"]
        last_price = m.get("last_price")
        pct = m.get("pct_change_vs_avg", 0)
        liquidity_note = f"Likuiditas avg: {human_idr(r['liquidity_avg_value'])}" if r["liquidity_avg_value"] else "Likuiditas: -"
        retail_note = human_idr(m["retail_net"]) if m.get("retail_net") is not None else "-"

        lines = []
        # first summary line: symbol — Asing Beli/Jual X/PERIOD (Label)
        buy_or_sell = "Beli" if net_as > 0 else "Jual" if net_as < 0 else "Netral"
        lines.append(f"*{sym}* — Asing {buy_or_sell} {m['streak']}/{PERIOD} hari ({r['label']})")
        lines.append(f"Rata-rata beli/jual asing: {human_idr(m.get('weighted_avg_price') or m.get('avg_price'))}")
        lines.append(f"Harga terakhir: {human_idr(last_price)} ({pct:+.1f}%)")
        lines.append(f"Net Asing ({PERIOD}d): {human_idr(net_as)} | Ritel: {retail_note}")
        lines.append(liquidity_note)
        # score + advice
        lines.append(f"ChanScore: {r['score']:.1f}/100 → {r['label']} ({r['advice']})")
        # divergence
        if r["divergence"]["flag"]:
            lines.append(f"🔄 Divergensi: Yes (corr={r['divergence']['corr']}) — {r['divergence']['explanation']}")
        else:
            lines.append(f"🔹 Divergensi: No (corr={r['divergence']['corr']})")
        if r["rec_buy"]:
            lines.append(f"💡 Rekomendasi BUY (area): {human_idr(r['rec_buy'])}")
        if r["rec_sell"]:
            lines.append(f"💡 Rekomendasi SELL/Take Profit (area): {human_idr(r['rec_sell'])}")
        if r["cut_loss"]:
            lines.append(f"🛑 Cut loss (saran): {human_idr(r['cut_loss'])}")
        # flexible guidance
        if r["trend"] == "Uptrend" and "Accumulation" in r["label"]:
            lines.append("⚠️ Uptrend & Asing masih akumulasi — fleksibel jual: gunakan trailing stop / sell on distribution.")
        body_lines.append("\n".join(lines) + "\n")

    report_text = header + "\n".join(body_lines)
    # append short notes about scoring interpretation
    report_text += "\n_Keterangan scoring_: ChanScore menggabungkan streak asing (45%), net-volume relatif (25%), stabilitas harga (15%), dan likuiditas (10%). Divergensi bisa menambah/mengurangi skor ±5._"
    return report_text
