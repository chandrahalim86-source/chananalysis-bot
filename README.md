# 📊 Smart Adaptive Pro v2.3 — Telegram Foreign Flow Analyzer

## 🔧 Fitur Utama
- Analisa otomatis **jam 18:00 WIB** setiap hari
- Analisa manual kapanpun via Telegram command `/analyze`
- Berdasarkan data **Foreign Buy/Sell & Harga (RTI/Stockbit)**
- Deteksi **divergensi asing vs ritel (early reversal)**
- **Interpretasi otomatis & fleksibel**
- Kirim laporan Telegram format teks profesional (20 saham teratas)

## 🧠 Parameter Environment

| Key | Value | Keterangan |
|-----|--------|------------|
| ANALYSIS_PERIOD | 15 | Periode analisa (hari) |
| TOP_N | 20 | Jumlah saham top akumulasi |
| MIN_LIQUIDITY_VALUE | 10000000000 | Filter likuiditas min Rp 10 M |
| SCHEDULE_UTC_EVENING | 11:00 | Jam 18:00 WIB |
| TELEGRAM_BOT_TOKEN | `xxxxxxxx` | Token bot kamu |
| TELEGRAM_CHAT_ID | `xxxxxxxx` | Chat ID kamu |

## 🚀 Cara Jalankan Manual
```bash
python main.py
