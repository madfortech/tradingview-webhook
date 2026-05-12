from flask import Flask, request
import json
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8325376679:AAEMAlcnYitaJiPGZFjch6wUWAYGLLBOjr4"
CHAT_ID = "7826747633"

last_signal = ""

@app.route("/")
def home():
return "TradingView Webhook Running"

@app.route("/webhook", methods=["POST"])
def webhook():

```
global last_signal

try:

    raw_data = request.data.decode("utf-8").strip()

    data = json.loads(raw_data)

    signal = str(data.get("signal", "SIGNAL"))

    symbol = str(data.get("symbol", "NIFTY"))

    try:
        price = float(data.get("price", 0))
    except:
        price = 0

    try:
        strike = int(float(data.get("strike", 0)))
    except:
        strike = 0

    time_now = str(
        data.get(
            "time",
            datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        )
    )

    current_key = f"{signal}_{symbol}_{strike}_{time_now}"

    if current_key == last_signal:
        return "duplicate", 200

    last_signal = current_key

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

    if market_type == "CRUDE":

        if option_type == "PE":
            trading_symbol = f"CRUDEOIL SELL {strike}"

        else:
            trading_symbol = f"CRUDEOIL BUY {strike}"

    else:

        trading_symbol = (
            f"{market_type} "
            f"{strike} "
            f"{option_type}"
        )

    telegram_message = f"""
```

🚨 {signal}

🌍 Market : {market_type}

🎯 Strike : {strike}

📈 Symbol : {trading_symbol}

💰 Live Price : {round(price, 2)}

⏰ Time : {time_now}
"""

```
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

    print(response.text)

    return "ok", 200

except Exception as e:

    print(str(e))

    return str(e), 500
```

if **name** == "**main**":
app.run(host="0.0.0.0", port=5000)
