from flask import Flask, request
import json
import requests
from datetime import datetime

# OPTIONAL SMART API LOGIN

try:

```
from SmartApi import SmartConnect
import pyotp

API_KEY = "YOUR_API_KEY"
CLIENT_CODE = "YOUR_CLIENT_CODE"
MPIN = "YOUR_MPIN"
TOTP_SECRET = "YOUR_TOTP_SECRET"

smartApi = SmartConnect(api_key=API_KEY)

totp = pyotp.TOTP(TOTP_SECRET).now()

session = smartApi.generateSession(
    CLIENT_CODE,
    MPIN,
    totp
)

print("✅ SMART API LOGIN SUCCESS")
```

except Exception as e:

```
print("❌ SMART API LOGIN FAILED")
print(str(e))
```

# =====================================

# 🚀 FLASK APP

# =====================================

app = Flask(**name**)

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

# 🏠 HOME ROUTE

# =====================================

@app.route("/")
def home():

```
return "TradingView Webhook Running"
```

# =====================================

# 🚨 WEBHOOK

# =====================================

@app.route("/webhook", methods=["POST"])
def webhook():

```
global last_signal

try:

    # =====================================
    # 📩 RAW DATA
    # =====================================

    raw_data = request.data.decode("utf-8").strip()

    print("\n==========================")
    print("📩 RAW WEBHOOK")
    print(raw_data)
    print("==========================\n")

    # =====================================
    # 🧠 JSON PARSE
    # =====================================

    try:

        data = json.loads(raw_data)

    except Exception as e:

        print("❌ JSON ERROR")
        print(str(e))

        return "bad json", 400

    # =====================================
    # 📊 DATA EXTRACTION
    # =====================================

    signal = str(
        data.get("signal", "SIGNAL")
    )

    symbol = str(
        data.get("symbol", "NIFTY")
    )

    # PRICE
    try:
        price = float(
            data.get("price", 0)
        )
    except:
        price = 0

    # STRIKE
    try:
        strike = int(
            float(
                data.get("strike", 0)
            )
        )
    except:
        strike = 0

    # TIME
    time_now = str(
        data.get(
            "time",
            datetime.now().strftime(
                "%d-%b-%Y %H:%M:%S"
            )
        )
    )

    # =====================================
    # 🚫 DUPLICATE BLOCKER
    # =====================================

    current_key = (
        f"{signal}_{symbol}_{strike}_{time_now}"
    )

    if current_key == last_signal:

        print("⚠️ DUPLICATE BLOCKED")

        return "duplicate", 200

    last_signal = current_key

    # =====================================
    # 🎯 OPTION TYPE DETECT
    # =====================================

    option_type = "CE"

    signal_upper = signal.upper()

    if (
        "SELL" in signal_upper or
        "SHORT" in signal_upper or
        "BEAR" in signal_upper or
        "PE" in signal_upper or
        "PUT" in signal_upper or
        "SUPPLY" in signal_upper or
        "HEDGE" in signal_upper
    ):

        option_type = "PE"

    # =====================================
    # 🌍 MARKET DETECTION
    # =====================================

    symbol_upper = symbol.upper()

    market_type = "NIFTY"

    if "BANKNIFTY" in symbol_upper:

        market_type = "BANKNIFTY"

    elif "FINNIFTY" in symbol_upper:

        market_type = "FINNIFTY"

    elif "SENSEX" in symbol_upper:

        market_type = "SENSEX"

    elif "BANKEX" in symbol_upper:

        market_type = "BANKEX"

    elif "CRUDE" in symbol_upper:

        market_type = "CRUDE"

    # =====================================
    # 📈 TRADING SYMBOL
    # =====================================

    if market_type == "CRUDE":

        if option_type == "PE":

            trading_symbol = (
                f"CRUDEOIL SELL {strike}"
            )

        else:

            trading_symbol = (
                f"CRUDEOIL BUY {strike}"
            )

    else:

        trading_symbol = (
            f"{market_type} "
            f"{strike} "
            f"{option_type}"
        )

    # =====================================
    # 📩 TELEGRAM MESSAGE
    # =====================================

    telegram_message = f"""
```

🚨 {signal}

📊 AUTO MARKET SIGNAL

🌍 Market : {market_type}

🎯 Strike : {strike}

📈 Symbol : {trading_symbol}

💰 Live Price : {round(price, 2)}

⏰ Time : {time_now}
"""

```
    print("\n📤 TELEGRAM MESSAGE")
    print(telegram_message)

    # =====================================
    # 📡 SEND TELEGRAM
    # =====================================

    telegram_url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
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

    print("\n✅ TELEGRAM RESPONSE")
    print(response.text)

    return "ok", 200

except Exception as e:

    print("\n❌ WEBHOOK ERROR")
    print(str(e))

    return str(e), 500
```

# =====================================

# 🚀 START SERVER

# =====================================

if **name** == "**main**":

```
app.run(
    host="0.0.0.0",
    port=5000
)
```
