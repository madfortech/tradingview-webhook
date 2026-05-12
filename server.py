from flask import Flask, request
import requests
import math
from datetime import datetime, timedelta

app = Flask(__name__)

# =========================
# TELEGRAM SETTINGS
# =========================

BOT_TOKEN = "8325376679:AAEMAlcnYitaJiPGZFjch6wUWAYGLLBOjr4"
CHAT_ID = "7826747633"

# =========================
# TELEGRAM SEND FUNCTION
# =========================

def send_telegram(msg):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# =========================
# AUTO EXPIRY DETECTION
# =========================

def get_expiry():

    today = datetime.now()

    days_ahead = 3 - today.weekday()

    if days_ahead <= 0:
        days_ahead += 7

    expiry = today + timedelta(days=days_ahead)

    return expiry.strftime("%d %b").upper()

# =========================
# WEBHOOK
# =========================

@app.route('/webhook', methods=['POST'])

def webhook():

    data = request.json

    signal = data.get("signal", "SIGNAL")

    # =========================
    # LIVE SPOT (TEMP MANUAL)
    # =========================

    spot = 24532

    # =========================
    # AUTO ATM STRIKE
    # =========================

    strike = round(spot / 50) * 50

    # =========================
    # OPTION TYPE
    # =========================

    optionType = "CE"

    bearishWords = [
        "BEAR",
        "SUPPLY",
        "SL HIT",
        "HEDGE"
    ]

    for word in bearishWords:

        if word in signal:
            optionType = "PE"

    # =========================
    # AUTO EXPIRY
    # =========================

    expiry = get_expiry()

    # =========================
    # FINAL TELEGRAM MESSAGE
    # =========================

    finalMessage = f"""
🚨 {signal}

📊 NIFTY OPTION SIGNAL

🎯 Strike: {strike} {optionType}

📅 Expiry: {expiry}

💰 Spot Price: {spot}
"""

    print(finalMessage)

    send_telegram(finalMessage)

    return "ok"

# =========================
# RUN SERVER
# =========================

app.run(host="127.0.0.1", port=8080)
