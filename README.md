# Foreign Flow Monitor (Telegram Bot)

Bot ini mengirimkan laporan *akumulasi & distribusi asing* di saham-saham likuid BEI.

---

## 🔧 Konfigurasi Environment (di Render)

| Variable | Deskripsi | Contoh |
|-----------|------------|--------|
| `BOT_TOKEN` | Token Telegram bot kamu | `123456:ABC-DEF...` |
| `CHAT_ID` | Chat ID penerima laporan | `123456789` |
| `ANALYSIS_PERIOD` | Periode analisa (hari) | `15` |
| `TOP_N` | Jumlah saham teratas dikirim | `20` |
| `MIN_LIQUIDITY_VALUE` | Likuiditas minimum | `10000000000` |
| `SCHEDULE_UTC_EVENING` | Jam kirim otomatis UTC | `11:00` (setara 18:00 WIB) |

---

## 🚀 Fitur
- Otomatis kirim laporan jam **18:00 WIB**
- Bisa jalankan manual via perintah Telegram:
/analyze
- Format laporan profesional, lengkap dengan kesimpulan otomatis dan saran tindakan.

---

## 🧩 Jalankan Lokal (Opsional)
```bash
pip install -r requirements.txt
python main.py

