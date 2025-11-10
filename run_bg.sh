#!/usr/bin/env bash
set -e
cd /cf_tg_bot
source ".venv/bin/activate"
echo "[INFO] Запускаю Telegram-бота..."
nohup python3 -u main.py >> logs/bot.log 2>&1 &
echo "[INFO] Запускаю Flask-панель (логи отключены)..."
nohup python3 -u web/app.py > /dev/null 2>&1 &
echo "[INFO] Всё запущено в фоне!"