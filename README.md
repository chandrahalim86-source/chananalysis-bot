# Chananalysis Bot — Smart Adaptive Pro Final (v3.0)

## Tujuan
Bot ini mengirimkan laporan harian akumulasi asing di IHSG (RTI primary + Stockbit fallback). Jadwal default: **18:00 WIB (11:00 UTC)**. Juga ada command `/analyze` untuk laporan on-demand.

## File penting
- `main.py` — entry point, runs Telegram bot and scheduler.
- `analyzer.py` — analysis logic, scoring, recommendation generator.
- `data_fetcher.py` — fetch data from RTI and Stockbit.
- `requirements.txt` — dependencies (use Python 3.12.7 on Render).
- `README.md` — (this file).

## Environment variables (set in Render -> Environment)
- `PYTHON_VERSION` = `3.12.7` (very important)
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `TELEGRAM_CHAT_ID` — chat ID to send daily reports
- `RTI_API_BASE` — optional, default `https://rtiapi.rti.co.id`
- `RTI_EMAIL`, `RTI_PASSWORD` — optional (if login needed)
- `ANALYSIS_PERIOD` — default `15`
- `TOP_N` — default `20`
- `MIN_LIQUIDITY_VALUE` — default `10000000000`
- `SCHEDULE_UTC_TIME_EVENING` — default `11:00` (11:00 UTC = 18:00 WIB)

## Deploy notes (Render)
1. Set repository to Render, set `PYTHON_VERSION` env to `3.12.7`.
2. Clear build cache (recommended) and then deploy latest commit.
3. Ensure port binding is present (main.py binds to port 10000 via hypercorn).
4. For free plan: keep as web service (not background worker). The web service keeps bot and scheduler alive.
5. Test: send `/start` and `/analyze` to bot to verify.

## Troubleshooting
- If pandas fails to build: ensure Python is 3.12.7 and rebuild with cleared cache.
- If Telegram shows `Conflict` error: make sure there is only one bot instance running (no other getUpdates in other deployments).
- Check logs in Render dashboard for exceptions.

## How to use
- `/start` — start help text
- `/analyze` — ask for an immediate report
- Daily report will be sent to `TELEGRAM_CHAT_ID` at scheduled UTC time.

## Notes about security
- Keep `TELEGRAM_BOT_TOKEN`, `RTI_EMAIL`, `RTI_PASSWORD` private. Do NOT paste into public channels.
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
