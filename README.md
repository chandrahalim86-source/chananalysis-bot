# Chananalysis Bot — Smart Adaptive Pro Final (v3.0)

## Tujuan
Kirim laporan harian akumulasi asing IHSG (RTI primary, Stockbit fallback). Jadwal default: 18:00 WIB (11:00 UTC). Ada perintah on-demand `/analyze`.

## File
- main.py
- analyzer.py
- data_fetcher.py
- requirements.txt

## Environment variables (Render)
- `PYTHON_VERSION` = `3.12.7`  ← penting
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `RTI_API_BASE` (optional, default used if empty)
- `RTI_EMAIL` (optional)
- `RTI_PASSWORD` (optional)
- `ANALYSIS_PERIOD` = `15`
- `TOP_N` = `20`
- `MIN_LIQUIDITY_VALUE` = `10000000000`
- `SCHEDULE_UTC_TIME_EVENING` = `11:00`

## Deploy steps (singkat)
1. Replace repo files with the above files.
2. In Render:
   - Set `PYTHON_VERSION=3.12.7`
   - Add the environment variables above (put secrets in env variables).
   - Clear build cache (Render option) and then Deploy Latest Commit.
3. After deploy: test Telegram `/start` and `/analyze`.

## Notes
- Gunakan only **one** bot instance (jika ada instance lain yang polling, matikan) untuk menghindari `Conflict` error.
- Jika ada error build `pandas`, pastikan Python version sudah 3.12.7 and clear cache.
