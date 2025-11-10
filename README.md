# Smart Adaptive Pro v3.0 – Final Stable
Bot analisis otomatis saham dengan fokus pada akumulasi asing dan kekuatan tren teknikal 15 hari terakhir.

## 🔍 Fitur Utama
- Analisa otomatis 20 saham dengan foreign accumulation tertinggi (15 hari terakhir)
- Penilaian ChanScore untuk deteksi akumulasi/distribusi
- Kesimpulan otomatis berbasis tren
- Jadwal kirim otomatis setiap hari jam 18:00 WIB ke Telegram
- Bisa juga dijalankan manual via endpoint `/analyze`

## 🚀 Cara Deploy di Render
1. Upload semua file (`main.py`, `analyzer.py`, `requirements.txt`, `README.md`)
2. Tambahkan environment variables:
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
Start command:
python main.py
Jalankan manual via browser:
https://your-app-url.onrender.com/analyze
## 📅 Jadwal
- Otomatis kirim laporan setiap hari pukul **18:00 WIB**
- Manual trigger: `/analyze`

## 📞 Output Format
- 20 saham dengan foreign accumulation tertinggi
- ChanScore dan interpretasi akurat
- Kesimpulan otomatis tiap saham
