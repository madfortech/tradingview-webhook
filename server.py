from flask import Flask, request
from SmartApi import SmartConnect
import pyotp
import requests
import json
from datetime import datetime

app = Flask(name)



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

```
global last_signal

try:

    # =====================================
    # 📩 RAW DATA
    # =====================================

    raw_data = request.data.decode("utf-8").strip()

    print("\n==========================")
    print("📩 RAW WEBHOOK:")
    print(raw_data)
    print("==========================\n")

    # =====================================
    # 🧠 SAFE JSON PARSE
    # =====================================

    try:
        data = json.loads(raw_data)

    except json.JSONDecodeError:

        print("❌ JSON PARSE FAILED")
        print(raw_data)

        return "bad json", 400

    # =====================================
    # 📊 DATA EXTRACTION
    # =====================================

    signal = str(data.get("signal", "SIGNAL"))

    symbol = str(data.get("symbol", "NIFTY"))

    try:
        price = float(data.get("price", 0))
    except:
        price = 0

    time_now = str(
        data.get(
            "time",
            datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")
        )
    )

    # =====================================
    # 🚫 DUPLICATE BLOCKER
    # =====================================

    current_key = f"{signal}_{symbol}_{price}_{time_now}"

    if current_key == last_signal:

        print("⚠️ DUPLICATE BLOCKED")

        return "duplicate blocked", 200

    last_signal = current_key

    # =====================================
    # 🎯 OPTION TYPE DETECT
    # =====================================

    option_type = "CE"

    signal_upper = signal.upper()

    if (
        "BEAR" in signal_upper or
        "PUT" in signal_upper or
        "PE" in signal_upper or
        "SELL" in signal_upper or
        "SHORT" in signal_upper or
        "HEDGE" in signal_upper or
        "SUPPLY" in signal_upper
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
    # 🎯 AUTO STRIKE LOGIC
    # =====================================

    if market_type == "BANKNIFTY":

        strike = round(price / 100) * 100

        trading_symbol = (
            f"BANKNIFTY {strike} {option_type}"
        )

    elif market_type == "FINNIFTY":

        strike = round(price / 50) * 50

        trading_symbol = (
            f"FINNIFTY {strike} {option_type}"
        )

    elif market_type == "SENSEX":

        strike = round(price / 100) * 100

        trading_symbol = (
            f"SENSEX {strike} {option_type}"
        )

    elif market_type == "BANKEX":

        strike = round(price / 100) * 100

        trading_symbol = (
            f"BANKEX {strike} {option_type}"
        )

    elif market_type == "CRUDE":

        strike = round(price / 100) * 100

        if option_type == "PE":

            trading_symbol = (
                f"CRUDEOIL SELL {strike}"
            )

        else:

            trading_symbol = (
                f"CRUDEOIL BUY {strike}"
            )

    else:

        strike = round(price / 50) * 50

        trading_symbol = (
            f"NIFTY {strike} {option_type}"
        )

    # =====================================
    # 📩 TELEGRAM MESSAGE
    # =====================================

    telegram_message = f"""
```

🚨 {signal}

📊 AUTO MARKET SIGNAL

🌍 Market : {market_type}

🎯 Option Type : {option_type}

🎯 Strike : {strike}

📈 Symbol : {trading_symbol}

💰 Live Price : {round(price, 2)}

⏰ Time : {time_now}
"""

```
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
