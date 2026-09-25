# Telegram Downloader Bot

## Render settings

Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
uvicorn bot:api --host 0.0.0.0 --port $PORT
```

Environment Variables:
- `BOT_TOKEN`
- `ADMIN_ID`

## Important
- MP3 needs FFmpeg available on the server.
- Some platforms may require cookies or external APIs.
- SQLite is suitable for testing; use PostgreSQL for production.
- This project is a starter implementation and has not been verified on your Render account.
