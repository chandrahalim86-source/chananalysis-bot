# 📈 Auto Stock Analyzer Pro v3.0

## ⚙️ Fitur Utama
- Analisa akumulasi / distribusi asing & ritel
- Deteksi divergensi asing-ritel (indikasi early reversal)
- ChanScore (indikator kekuatan tren)
- Kesimpulan otomatis (hold, take profit, buy weakness, dll)
- Laporan otomatis dikirim setiap jam **18:00 WIB**
- Perintah manual via `/analyze` untuk update kapanpun

## 🧩 Environment Variables
| Nama | Deskripsi | Default |
|------|------------|----------|
| TELEGRAM_TOKEN | Token bot Telegram kamu | - |
| CHAT_ID | ID grup atau user Telegram penerima laporan | - |
| ANALYSIS_PERIOD | Jumlah hari analisa | 15 |
| TOP_N | Jumlah saham tertinggi yang ditampilkan | 20 |
| SCHEDULE_UTC_EVENING | Jam UTC untuk laporan sore (18:00 WIB = 11:00) | 11:00 |
| TIMEZONE | Zona waktu lokal | Asia/Jakarta |

## 🚀 Cara Jalankan
1. Upload semua file (`main.py`, `analyzer.py`, `requirements.txt`, `README.md`) ke Render.
2. Masukkan semua variabel environment di atas.
3. Deploy → Bot otomatis kirim laporan jam 18:00 WIB setiap hari bursa.
4. Bisa jalankan manual via Telegram dengan perintah:  
