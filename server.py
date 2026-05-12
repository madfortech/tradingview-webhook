from flask import Flask, request
from SmartApi import SmartConnect
import pyotp
import requests
import json
from datetime import datetime

app = Flask(__name__)

# =====================================
# 🔐 ANGEL ONE LOGIN
# =====================================

API_KEY = "6mZMklIr"

CLIENT_CODE = "JANAK4986"

MPIN = "1989"

TOTP_SECRET = "KBUFFEP4QAVYBR6OPRPWZSYORI"

smartApi = SmartConnect(api_key=API_KEY)

totp = pyotp.TOTP(TOTP_SECRET).now()

session = smartApi.generateSession(
    CLIENT_CODE,
    MPIN,
    totp
)

print("\n✅ ANGEL LOGIN SUCCESS")

# =====================================
# 🔐 TELEGRAM
# =====================================

BOT_TOKEN = "8325376679:AAEMAlcnYitaJiPGZFjch6wUWAYGLLBOjr4"

CHAT_ID = "7826747633"

# =====================================
# 🚫 DUPLICATE FILTER
# =====================================

last_signal = ""

# =====================================
# 🏠 HOME
# =====================================

@app.route("/")
def home():
    return "🚀 TradingView Webhook Running"

# =====================================
# 🚨 WEBHOOK
# =====================================

@app.route("/webhook", methods=["POST"])
def webhook():

    global last_signal

    try:

        # =====================================
        # 📩 RAW DATA
        # =====================================

        raw_data = request.data.decode("utf-8")

        print("\n==========================")
        print("📩 RAW WEBHOOK:")
        print(raw_data)
        print("==========================\n")

        # =====================================
        # 🧠 JSON PARSE
        # =====================================

        data = json.loads(raw_data)

        signal = data.get("signal", "SIGNAL")

        symbol = data.get("symbol", "NIFTY")

        price = float(data.get("price", 0))

        time_now = data.get(
            "time",
            datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")
        )

        # =====================================
        # 🚫 DUPLICATE BLOCKER
        # =====================================

        current_key = f"{signal}_{symbol}_{price}"

        if current_key == last_signal:

            print("⚠️ DUPLICATE BLOCKED")

            return "duplicate blocked", 200

        last_signal = current_key

        # =====================================
        # 🎯 OPTION TYPE DETECT
        # =====================================

        option_type = "CE"

        if (
            "BEAR" in signal or
            "PUT" in signal or
            "PE" in signal or
            "HEDGE" in signal or
            "SUPPLY" in signal
        ):
            option_type = "PE"

        # =====================================
        # 🎯 AUTO STRIKE
        # =====================================

        strike = round(price / 50) * 50

        trading_symbol = f"NIFTY {strike} {option_type}"

        # =====================================
        # 🧾 TELEGRAM MESSAGE
        # =====================================

        telegram_message = f"""
🚨 {signal}

📊 AUTO OPTION SIGNAL

🎯 Option Type : {option_type}
🎯 Strike      : {strike}

📈 Symbol      : {trading_symbol}

💰 Live Spot   : {price}

⏰ Time : {time_now}
"""

        print("\n📤 TELEGRAM MESSAGE:")
        print(telegram_message)

        # =====================================
        # 📡 SEND TELEGRAM
        # =====================================

        telegram_url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        )

        payload = {
            "chat_id": CHAT_ID,
            "text": telegram_message
        }

        response = requests.post(
            telegram_url,
            json=payload,
            timeout=10
        )

        print("\n✅ TELEGRAM RESPONSE:")
        print(response.text)

        return "ok", 200

    except Exception as e:

        print("\n❌ WEBHOOK ERROR")
        print(str(e))

        return f"error: {str(e)}", 500

# =====================================
# 🚀 START SERVER
# =====================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
