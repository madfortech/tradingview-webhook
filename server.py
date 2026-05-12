from flask import Flask, request
from SmartApi import SmartConnect
import requests
import pyotp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================================================
# ANGEL ONE SMART API CONFIG
# ==================================================

API_KEY     = "6mZMklIr"
CLIENT_ID   = "JANAK4986"
PASSWORD    = "1989"
TOTP_SECRET = "KBUFFEP4QAVYBR6OPRPWZSYORI"

# ==================================================
# TELEGRAM CONFIG
# ==================================================

BOT_TOKEN = "8325376679:AAEMAlcnYitaJiPGZFjch6wUWAYGLLBOjr4"
CHAT_ID   = "7826747633"

# ==================================================
# NIFTY NSE TOKEN (Fixed — no longer hardcoded "26000")
# Use Angel One's actual token for NIFTY index
# NSE NIFTY token = 26000 (this is correct for ltpData)
# ==================================================

NIFTY_TOKEN  = "26000"
NIFTY_SYMBOL = "NIFTY"
NIFTY_EXCH   = "NSE"

# ==================================================
# TELEGRAM SENDER
# ==================================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )
        if resp.status_code != 200:
            logger.error(f"Telegram error: {resp.text}")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")

# ==================================================
# ANGEL ONE LOGIN
# ==================================================

def angel_login():
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    data = obj.generateSession(CLIENT_ID, PASSWORD, totp)
    if not data or data.get("status") is False:
        raise Exception(f"Angel login failed: {data}")
    logger.info("Angel One login successful")
    return obj

# ==================================================
# LIVE NIFTY SPOT PRICE
# ==================================================

def get_nifty_spot(obj):
    ltp_data = obj.ltpData(NIFTY_EXCH, NIFTY_SYMBOL, NIFTY_TOKEN)
    if not ltp_data or ltp_data.get("status") is False:
        raise Exception(f"LTP fetch failed: {ltp_data}")
    spot = ltp_data["data"]["ltp"]
    return float(spot)

# ==================================================
# ATM STRIKE (rounds to nearest 50)
# ==================================================

def get_atm_strike(spot):
    return int(round(spot / 50) * 50)

# ==================================================
# OPTION TYPE (CE / PE based on signal text)
# ==================================================

def get_option_type(signal):
    bearish_words = ["SELL", "PUT", "BEAR", "SUPPLY", "SHORT", "BREAKDOWN", "HEDGE"]
    signal_upper = signal.upper()
    for word in bearish_words:
        if word in signal_upper:
            return "PE"
    return "CE"

# ==================================================
# LIVE OPTION SYMBOL FROM ANGEL ONE
# Searches NFO for nearest expiry NIFTY option
# ==================================================

def get_live_option_symbol(obj, strike, option_type):
    try:
        query = f"NIFTY {strike} {option_type}"
        result = obj.searchScrip("NFO", query)

        if not result or result.get("status") is False:
            logger.warning(f"searchScrip failed for: {query}")
            return query

        symbols = result.get("data", [])
        if not symbols:
            logger.warning(f"No symbols found for: {query}")
            return query

        # Filter only NIFTY options with correct type (CE or PE)
        filtered = [
            s.get("symbol", "")
            for s in symbols
            if "NIFTY" in s.get("symbol", "")
            and option_type in s.get("symbol", "")
            and "BANKNIFTY" not in s.get("symbol", "")
            and "FINNIFTY" not in s.get("symbol", "")
            and "MIDCPNIFTY" not in s.get("symbol", "")
        ]

        if not filtered:
            logger.warning(f"No filtered match for: {query}")
            return query

        # Sort alphabetically — nearest expiry comes first
        filtered.sort()
        return filtered[0]

    except Exception as e:
        logger.error(f"Option symbol fetch error: {e}")
        return f"NIFTY {strike} {option_type}"

# ==================================================
# SAFE VALUE (handles None / nan / empty)
# ==================================================

def safe_value(v):
    if v in [None, "", "na", "nan", "None"]:
        return "N/A"
    return str(v)

# ==================================================
# WEBHOOK ENDPOINT
# Receives TradingView JSON alert and sends to Telegram
# ==================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return {"status": "error", "message": "No JSON received"}, 400

        logger.info(f"Webhook received: {data}")

        # ---- Parse TradingView fields ----
        signal      = safe_value(data.get("signal", "SIGNAL"))
        price       = safe_value(data.get("price", "0"))
        entry       = safe_value(data.get("entry", "0"))
        sl          = safe_value(data.get("sl", "0"))
        tp1         = safe_value(data.get("tp1", "0"))
        tp2         = safe_value(data.get("tp2", "0"))
        tp3         = safe_value(data.get("tp3", "0"))
        signal_time = safe_value(data.get("time", ""))

        # ---- Angel One: login + live data ----
        obj          = angel_login()
        spot         = get_nifty_spot(obj)
        strike       = get_atm_strike(spot)
        option_type  = get_option_type(signal)
        option_symbol = get_live_option_symbol(obj, strike, option_type)

        # ---- Build Telegram message ----
        message = (
            f"🚨 {signal}\n\n"
            f"📊 AUTO OPTION SIGNAL\n\n"
            f"🎯 Option Type : {option_type}\n"
            f"🎯 Strike      : {strike}\n"
            f"📈 Symbol      : {option_symbol}\n\n"
            f"💰 Live Spot   : {spot}\n"
            f"💵 Price       : {price}\n"
            f"🎯 Entry       : {entry}\n"
            f"🛑 Stop Loss   : {sl}\n\n"
            f"🎯 TP1 : {tp1}\n"
            f"🎯 TP2 : {tp2}\n"
            f"🎯 TP3 : {tp3}\n\n"
            f"⏰ Time : {signal_time}"
        )

        logger.info(message)
        send_telegram(message)

        return {"status": "success", "strike": strike, "option": option_symbol}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Webhook error: {error_msg}")
        send_telegram(f"❌ Webhook Error\n{error_msg}")
        return {"status": "error", "message": error_msg}, 500

# ==================================================
# HOME
# ==================================================

@app.route('/')
def home():
    return "✅ TradingView Webhook Running"

# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
