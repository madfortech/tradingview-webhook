from flask import Flask, request, jsonify
import requests
import json
import time
from datetime import datetime
from threading import Thread

app = Flask(__name__)

# =========================
# TELEGRAM CONFIG
# =========================

BOT_TOKEN = "8325376679:AAEMAlcnYitaJiPGZFjch6wUWAYGLLBOjr4"
CHAT_ID = "7826747633"

# =========================
# DUPLICATE MEMORY
# =========================

last_signal = ""

# =========================
# HOME ROUTE
# =========================

@app.route("/")
def home():
    return "🚀 TradingView Webhook Running"

# =========================
# TELEGRAM SENDER
# =========================

def send_telegram_message(payload, telegram_url):

    try:

        response = requests.post(
            telegram_url,
            json=payload,
            timeout=5
        )

        print("✅ TELEGRAM SENT")
        print(response.text)

    except Exception as e:

        print("❌ TELEGRAM ERROR")
        print(str(e))

# =========================
# WEBHOOK
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():

    global last_signal

    try:

        # =========================
        # RAW DATA
        # =========================

        raw_data = request.data.decode("utf-8").strip()

        print("\n==============================")
        print("📩 NEW WEBHOOK RECEIVED")
        print("==============================")
        print(raw_data)

        # =========================
        # JSON PARSE
        # =========================

        data = json.loads(raw_data)

        # =========================
        # SIGNAL
        # =========================

        signal = str(data.get("signal", "SIGNAL"))
        symbol = str(data.get("symbol", "NIFTY"))

        # =========================
        # PRICE
        # =========================

        try:
            price = float(data.get("price", 0))
        except:
            price = 0

        # =========================
        # STRIKE
        # =========================

        try:
            strike = int(float(data.get("strike", 0)))
        except:
            strike = 0

        # =========================
        # ENTRY / SL / TARGET
        # =========================

        try:
            entry = float(data.get("entry", 0))
        except:
            entry = 0

        try:
            sl = float(data.get("sl", 0))
        except:
            sl = 0

        try:
            target = float(data.get("target", 0))
        except:
            target = 0

        # =========================
        # TIMEFRAME
        # =========================

        timeframe = str(data.get("timeframe", "5m"))

        # =========================
        # TIME
        # =========================

        time_now = str(
            data.get(
                "time",
                datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            )
        )

        # =========================
        # DUPLICATE FILTER
        # =========================

        current_key = f"{signal}_{symbol}_{strike}_{round(price,2)}"

        if current_key == last_signal:

            print("⚠️ DUPLICATE ALERT BLOCKED")

            return jsonify({
                "status": "duplicate"
            }), 200

        last_signal = current_key

        # =========================
        # OPTION TYPE
        # =========================

        option_type = "CE"

        signal_upper = signal.upper()

        if (
            "SELL" in signal_upper or
            "SHORT" in signal_upper or
            "BEAR" in signal_upper or
            "PE" in signal_upper or
            "PUT" in signal_upper or
            "SUPPLY" in signal_upper
        ):

            option_type = "PE"

        elif "HEDGE" in signal_upper:

            option_type = "INFO"

        # =========================
        # MARKET DETECTION
        # =========================

        symbol_upper = symbol.upper()

        market_type = "NIFTY"

        if "BANKNIFTY" in symbol_upper:
            market_type = "BANKNIFTY"

        elif "FINNIFTY" in symbol_upper:
            market_type = "FINNIFTY"

        elif "SENSEX" in symbol_upper:
            market_type = "SENSEX"

        elif "CRUDE" in symbol_upper:
            market_type = "CRUDE"

        # =========================
        # TRADING SYMBOL
        # =========================

        if market_type == "CRUDE":

            if option_type == "PE":

                trading_symbol = f"CRUDEOIL SELL {strike}"

            elif option_type == "INFO":

                trading_symbol = f"CRUDEOIL HEDGE {strike}"

            else:

                trading_symbol = f"CRUDEOIL BUY {strike}"

        else:

            trading_symbol = (
                f"{market_type} "
                f"{strike} "
                f"{option_type}"
            )

        # =========================
        # TELEGRAM MESSAGE
        # =========================

        telegram_message = f"""
🚨 {signal}

🌍 Market : {market_type}

🎯 Strike : {strike}

📈 Symbol : {trading_symbol}

🕒 TF : {timeframe}

📈 Entry : {entry}

🛑 SL : {sl}

🎯 Target : {target}

💰 Live Price : {round(price, 2)}

⏰ Time : {time_now}
"""

        # =========================
        # TELEGRAM API
        # =========================

        telegram_url = (
            f"https://api.telegram.org/bot"
            f"{BOT_TOKEN}/sendMessage"
        )

        payload = {
            "chat_id": CHAT_ID,
            "text": telegram_message
        }

        # =========================
        # BACKGROUND THREAD
        # =========================

        Thread(
            target=send_telegram_message,
            args=(payload, telegram_url)
        ).start()

        # =========================
        # INSTANT RESPONSE
        # =========================

        return jsonify({
            "status": "success"
        }), 200

    except Exception as e:

        print("\n❌ WEBHOOK ERROR")
        print(str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
