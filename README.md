# Chananalysis Bot 📈

Bot Telegram otomatis untuk analisa harian saham Indonesia (IHSG) berdasarkan akumulasi beli asing dan bandar.

## 🧠 Fitur Utama
- Mengambil data akumulasi beli/jual asing & bandar (RTI/BEI/Stockbit)
- Mengirim laporan otomatis ke Telegram setiap hari pukul 18:00 WIB
- Berjalan otomatis di cloud (Render.com)

## ⚙️ Teknologi
- Python 3
- Library: `requests`, `schedule`
- Telegram Bot API
- Render (free cloud hosting)

## 🚀 Cara Kerja
1. Mengambil data akumulasi asing dari API sumber data
2. Menganalisis saham dengan akumulasi positif minimal 1 minggu
3. Mengirim hasil ke channel/pesan Telegram via bot

## 🗓 Jadwal
Bot dijadwalkan otomatis setiap hari:
- **Jam 18:00 WIB (11:00 UTC)**

## 👤 Owner
Bot ini dibuat untuk **@Chan7878Bot**  
Channel analisis: *Chananalysis7878*

---

> Dikembangkan oleh Chandra Halim  
> Untuk keperluan riset dan monitoring saham otomatis.

