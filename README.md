# 📊 Telegram Auto Stock Analyzer — Profesional Edition

Bot otomatis untuk menganalisis pergerakan saham di IDX (Indonesia Stock Exchange) dengan indikator:
- Akumulasi / Distribusi asing
- Divergensi asing vs ritel
- Kesimpulan otomatis (rekomendasi hold / take profit / reduce)
- Penjadwalan otomatis (scheduler)
- Perintah manual `/analyze`

---

## ⚙️ Environment Variables
Wajib diisi di Render (Environment tab):

| Variable | Deskripsi | Contoh |
|-----------|------------|--------|
| `TELEGRAM_TOKEN` | Token bot Telegram | `123456:ABC...` |
| `CHAT_ID` | Chat ID tujuan laporan | `-100123456789` |
| `ANALYSIS_PERIOD` | Periode analisis (hari) | `15` |
| `TOP_N` | Jumlah saham teratas yang dianalisis | `20` |
| `MIN_LIQUIDITY_VALUE` | Filter minimum likuiditas | `10000000000` |
| `SCHEDULE_UTC_EVENING` | Jadwal UTC untuk 18:00 WIB | `11` |

---

## 🕒 Jadwal Analisa Otomatis
Bot akan otomatis kirim laporan setiap hari jam **18:00 WIB (11:00 UTC)**.  
Laporan berisi 20 saham teratas dengan format terstruktur.

---

## 💬 Perintah Manual
Ketik di Telegram:
/analyze
untuk memicu laporan kapanpun secara langsung.

---

## 🧱 Cara Deploy di Render
1. Upload semua file (`main.py`, `analyzer.py`, `requirements.txt`, `README.md`)
2. Isi Environment Variables sesuai tabel di atas
3. Clear Build Cache → Redeploy
4. Selesai ✅
