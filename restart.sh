#!/usr/bin/env bash
set -e

cd /cf_tg_bot

echo "[INFO] Ищу запущенный процесс бота..."
pid=$(ps -ef | grep "python3 -u main.py" | grep -v grep | awk '{print $2}')

if [ -n "$pid" ]; then
    echo "[INFO] Останавливаю процесс $pid"
    kill -9 $pid
    sleep 2
else
    echo "[INFO] Бот не был запущен."
fi

echo "[INFO] Запускаю бота..."
nohup ./run_bg.sh > logs/restart.log 2>&1 &

echo "[INFO] Перезапуск завершён."
