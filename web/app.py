from flask import Flask, render_template_string, redirect, url_for, request
import subprocess
import os

app = Flask(__name__)

LOG_PATH = "/cf_tg_bot/logs/bot.log"
RESTART_SCRIPT = "/cf_tg_bot/restart.sh"
ADMIN_TOKEN = os.getenv("WEB_ADMIN_TOKEN")

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Bot Control Panel</title>
  <style>
    body { font-family: sans-serif; margin: 20px; background: #f9f9f9; }
    pre { background: #222; color: #0f0; padding: 10px; border-radius: 6px; max-height: 70vh; overflow: auto; }
    button { padding: 10px 20px; font-size: 16px; margin-top: 10px; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Bot Control Panel</h1>
  <form method="POST" action="/restart?token={{ token }}">
    <button type="submit">🔁 Перезапустить бота</button>
  </form>
  <h2>Логи:</h2>
  <pre>{{ logs }}</pre>
</body>
</html>
"""

@app.before_request
def check_auth():
    token = request.args.get("token")
    if token != ADMIN_TOKEN:
        return "403 Forbidden", 403

@app.route("/")
def index():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            logs = "".join(f.readlines()[-300:])
    except FileNotFoundError:
        logs = "Лог-файл не найден"
    return render_template_string(HTML, logs=logs, token=ADMIN_TOKEN)

@app.route("/restart", methods=["POST"])
def restart():
    subprocess.run(["bash", RESTART_SCRIPT])
    return redirect(url_for("index", token=ADMIN_TOKEN))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
