from flask import Flask, request
from SmartApi import SmartConnect
import requests
import pyotp
from datetime import datetime, timedelta

app = Flask(__name__)

# ==================================================
# ANGEL ONE SMART API
# ==================================================

API_KEY = "6mZMklIr"

CLIENT_ID = "JANAK4986"

PASSWORD = "1989"

TOTP_SECRET = "KBUFFEP4QAVYBR6OPRPWZSYORI"

# ==================================================
# TELEGRAM
# ==================================================

BOT_TOKEN = "8325376679:AAEMAlcnYitaJiPGZFjch6wUWAYGLLBOjr4"

CHAT_ID = "7826747633"

# ==================================================
# TELEGRAM FUNCTION
# ==================================================

def send_telegram(message):

    telegram_url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        }
    )

# ==================================================
# ANGEL LOGIN
# ==================================================

def angel_login():

    obj = SmartConnect(api_key=API_KEY)

    totp = pyotp.TOTP(TOTP_SECRET).now()

    session = obj.generateSession(
        CLIENT_ID,
        PASSWORD,
        totp
    )

    print("Angel Login Success")

    return obj

# ==================================================
# LIVE NIFTY SPOT
# ==================================================

def get_nifty_spot(obj):

    ltp = obj.ltpData(
        "NSE",
        "NIFTY",
        "26000"
    )

    spot = ltp["data"]["ltp"]

    return spot

# ==================================================
# AUTO EXPIRY
# ==================================================

def get_expiry():

    today = datetime.now()

    days_ahead = 3 - today.weekday()

    if days_ahead <= 0:
        days_ahead += 7

    expiry = today + timedelta(days=days_ahead)

    return expiry.strftime("%d %b").upper()

# ==================================================
# OPTION TYPE
# ==================================================

def get_option_type(signal):

    bearish_words = [
        "SELL",
        "PUT",
        "BEAR",
        "SUPPLY",
        "SHORT"
    ]

    for word in bearish_words:

        if word in signal.upper():

            return "PE"

    return "CE"

# ==================================================
# WEBHOOK ROUTE
# ==================================================

@app.route('/webhook', methods=['POST'])

def webhook():

    try:

        # ==========================================
        # RECEIVE TRADINGVIEW DATA
        # ==========================================

        data = request.json

        signal = data.get("signal", "SIGNAL")

        entry = data.get("entry", "0")

        sl = data.get("sl", "0")

        tp1 = data.get("tp1", "0")

        # ==========================================
        # ANGEL LOGIN
        # ==========================================

        obj = angel_login()

        # ==========================================
        # LIVE SPOT
        # ==========================================

        spot = get_nifty_spot(obj)

        # ==========================================
        # AUTO ATM STRIKE
        # ==========================================

        strike = round(spot / 50) * 50

        # ==========================================
        # OPTION TYPE
        # ==========================================

        option_type = get_option_type(signal)

        # ==========================================
        # AUTO EXPIRY
        # ==========================================

        expiry = get_expiry()

        # ==========================================
        # FINAL TELEGRAM MESSAGE
        # ==========================================

        final_message = f"""
🚨 {signal}

📊 AUTO OPTION SIGNAL

🎯 Strike:
NIFTY {strike} {option_type}

📅 Expiry:
{expiry}

💰 Spot:
{spot}

💵 Entry:
{entry}

🛑 Stop Loss:
{sl}

🎯 Target:
{tp1}
"""

        print(final_message)

        # ==========================================
        # SEND TELEGRAM
        # ==========================================

        send_telegram(final_message)

        return {
            "status": "success"
        }

    except Exception as e:

        print(str(e))

        return {
            "status": "error",
            "message": str(e)
        }

# ==================================================
# RUN SERVER
# ==================================================

app.run(
    host="0.0.0.0",
    port=10000
)
