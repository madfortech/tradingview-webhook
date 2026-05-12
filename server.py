from flask import Flask, request
from SmartApi import SmartConnect
import requests
import pyotp
import logging
import time
from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================================================
# ANGEL ONE CONFIG
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
# NIFTY CONSTANTS
# ==================================================

NIFTY_TOKEN  = "26000"
NIFTY_SYMBOL = "NIFTY"
NIFTY_EXCH   = "NSE"

# ==================================================
# DUPLICATE SIGNAL BLOCKER
# Same signal 60 seconds ke andar dobara aaye toh block
# ==================================================

last_signal_time = {}
DUPLICATE_WINDOW = 60  # seconds

def is_duplicate(signal_key):
    now = time.time()
    if signal_key in last_signal_time:
        if now - last_signal_time[signal_key] < DUPLICATE_WINDOW:
            return True
    last_signal_time[signal_key] = now
    return False

# ==================================================
# IST TIME
# ==================================================

def get_ist_time():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    return now.strftime("%d-%b-%Y %H:%M:%S IST")

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
# LIVE NIFTY SPOT
# ==================================================

def get_nifty_spot(obj):
    ltp_data = obj.ltpData(NIFTY_EXCH, NIFTY_SYMBOL, NIFTY_TOKEN)
    if not ltp_data or ltp_data.get("status") is False:
        raise Exception(f"LTP fetch failed: {ltp_data}")
    return float(ltp_data["data"]["ltp"])

# ==================================================
# ATM STRIKE
# ==================================================

def get_atm_strike(spot):
    return int(round(spot / 50) * 50)

# ==================================================
# OPTION TYPE
# ==================================================

def get_option_type(signal):
    bearish_words = ["SELL", "PUT", "BEAR", "SUPPLY", "SHORT",
                     "BREAKDOWN", "HEDGE", "SUPPLY ZONE"]
    for word in bearish_words:
        if word in signal.upper():
            return "PE"
    return "CE"

# ==================================================
# LIVE OPTION SYMBOL
# ==================================================

def get_live_option_symbol(obj, strike, option_type):
    try:
        query = f"NIFTY {strike} {option_type}"
        result = obj.searchScrip("NFO", query)

        if not result or result.get("status") is False:
            return query

        symbols = result.get("data", [])
        filtered = [
            s.get("symbol", "")
            for s in symbols
            if "NIFTY" in s.get("symbol", "")
            and option_type in s.get("symbol", "")
            and "BANKNIFTY"   not in s.get("symbol", "")
            and "FINNIFTY"    not in s.get("symbol", "")
            and "MIDCPNIFTY"  not in s.get("symbol", "")
        ]

        if not filtered:
            return query

        filtered.sort()
        return filtered[0]

    except Exception as e:
        logger.error(f"Option symbol error: {e}")
        return f"NIFTY {strike} {option_type}"

# ==================================================
# SAFE VALUE
# ==================================================

def safe_value(v):
    if v in [None, "", "na", "nan", "None", "N/A"]:
        return "N/A"
    return str(v)

def safe_float(v):
    try:
        return float(v)
    except:
        return None

# ==================================================
# FIX PE ENTRY / SL / TP
#
# TradingView Pine Script sends CE-side values
# for spot price (entry/sl/tp are Nifty index levels).
# For PE option, when Nifty goes DOWN, PE goes UP.
# So we recalculate targets correctly for PE.
#
# Logic:
#   entry_f  = Nifty spot at signal time
#   For PE:  market should go DOWN
#   SL       = entry + risk (above entry)
#   TP1/2/3  = entry - risk*RR (below entry)
# ==================================================

def fix_pe_levels(entry, sl, tp1, tp2, tp3, option_type, spot):
    entry_f = safe_float(entry)
    sl_f    = safe_float(sl)
    tp1_f   = safe_float(tp1)
    tp2_f   = safe_float(tp2)
    tp3_f   = safe_float(tp3)

    if None in [entry_f, sl_f, tp1_f, tp2_f, tp3_f]:
        return entry, sl, tp1, tp2, tp3

    if option_type == "PE":
        # Use spot as real entry reference
        ref = spot if spot else entry_f

        # Risk = distance TradingView gave as SL
        # (original SL was above entry for CE — use that gap as risk)
        risk = abs(sl_f - entry_f)
        if risk < 1:
            risk = ref * 0.002  # fallback: 0.2% of spot

        # PE correct levels: market goes DOWN
        real_entry = ref
        real_sl    = round(ref + risk, 2)        # SL above spot
        real_tp1   = round(ref - risk * 0.9, 2)  # TP1 below
        real_tp2   = round(ref - risk * 1.6, 2)  # TP2 further
        real_tp3   = round(ref - risk * 2.5, 2)  # TP3 furthest

        return (
            str(real_entry),
            str(real_sl),
            str(real_tp1),
            str(real_tp2),
            str(real_tp3)
        )

    # CE — return as-is
    return entry, sl, tp1, tp2, tp3

# ==================================================
# WEBHOOK
# ==================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return {"status": "error", "message": "No JSON received"}, 400

        logger.info(f"Webhook received: {data}")

        # ---- Parse fields ----
        signal = safe_value(data.get("signal", "SIGNAL"))
        price  = safe_value(data.get("price", "0"))
        entry  = safe_value(data.get("entry", "0"))
        sl     = safe_value(data.get("sl", "0"))
        tp1    = safe_value(data.get("tp1", "0"))
        tp2    = safe_value(data.get("tp2", "0"))
        tp3    = safe_value(data.get("tp3", "0"))

        # ---- DUPLICATE CHECK ----
        # Use signal + rounded price as unique key
        signal_key = f"{signal}_{round(safe_float(price) or 0, -1)}"
        if is_duplicate(signal_key):
            logger.info(f"Duplicate blocked: {signal_key}")
            return {"status": "duplicate", "message": "blocked"}, 200

        # ---- IST Time (ignore TradingView time) ----
        ist_time = get_ist_time()

        # ---- Angel One ----
        obj           = angel_login()
        spot          = get_nifty_spot(obj)
        strike        = get_atm_strike(spot)
        option_type   = get_option_type(signal)
        option_symbol = get_live_option_symbol(obj, strike, option_type)

        # ---- Fix PE levels ----
        entry, sl, tp1, tp2, tp3 = fix_pe_levels(
            entry, sl, tp1, tp2, tp3, option_type, spot
        )

        # ---- Telegram message ----
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
            f"⏰ Time : {ist_time}"
        )

        logger.info(message)
        send_telegram(message)

        return {
            "status": "success",
            "strike": strike,
            "option": option_symbol,
            "type": option_type
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Webhook error: {error_msg}")
        send_telegram(f"❌ Webhook Error\n{error_msg}\n⏰ {get_ist_time()}")
        return {"status": "error", "message": error_msg}, 500

# ==================================================
# HOME
# ==================================================

@app.route('/')
def home():
    return "✅ SecondEye Webhook Server Running"

# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
