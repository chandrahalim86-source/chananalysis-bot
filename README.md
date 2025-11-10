# 📈 Auto Stock Analyzer Pro v3.1 (Final Stable)

### 🚀 Fitur
- Analisa akumulasi/distribusi asing & ritel (15 hari)
- Deteksi divergensi asing–ritel (indikasi reversal)
- ChanScore (kekuatan tren)
- Kesimpulan otomatis cerdas (buy, hold, sell, warning)
- Kirim laporan otomatis jam **18:00 WIB**
- Perintah manual `/analyze` untuk analisa kapanpun

### ⚙️ Environment Variables
| Variable | Fungsi | Default |
|-----------|---------|----------|
| TELEGRAM_TOKEN | Token bot Telegram kamu | - |
| CHAT_ID | Chat ID tujuan (user/grup) | - |
| ANALYSIS_PERIOD | Hari analisa | 15 |
| TOP_N | Jumlah saham tertinggi | 20 |
| SCHEDULE_UTC_EVENING | Waktu UTC laporan sore (11:00 = 18:00 WIB) | 11:00 |
| TIMEZONE | Zona waktu | Asia/Jakarta |

### 💬 Perintah Telegram
/analyze
→ Jalankan analisa manual dan kirim laporan langsung ke chat.

### 🕒 Otomatis
Bot akan kirim laporan setiap jam 18:00 WIB.

### 📩 Format Laporan
📊 Laporan Akumulasi Asing (15 Hari)
Generated: 2025-11-10 18:00 WIB
Top 20 Saham Likuid

TLKM — Asing jual 8/15 hari (Distribusi)
Rata-rata beli/jual asing: Rp 3,120
Harga terakhir: Rp 3,070 (-1.6%)
Net Asing (10d): Rp -84.0M | Ritel: Rp +77.0M
Likuiditas avg: Rp 15.0B
ChanScore: 42.3/100 → Downtrend
🔄 Divergensi: Yes (corr=-0.68)
📈 Kesimpulan: Asing distribusi tapi ada divergensi kuat...
