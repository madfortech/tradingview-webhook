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
last_signal_time = 0

# =========================
# HOME ROUTE (Keep-Alive ping bhi yahi se hoga)
# =========================

@app.route("/")
def home():
    return "🚀 TradingView Webhook Running", 200

@app.route("/ping")
def ping():
    return "pong", 200

# =========================
# TELEGRAM SENDER
# =========================

def send_telegram_message(text):
    try:
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(telegram_url, json=payload, timeout=10)
        print(f"✅ TELEGRAM SENT | Status: {response.status_code}")
        print(response.text)
    except Exception as e:
        print(f"❌ TELEGRAM ERROR: {str(e)}")

# =========================
# SAFE JSON PARSE
# Handles both JSON and plain text from TradingView
# =========================

def safe_parse(raw):
    raw = raw.strip()

    # 1️⃣ Try direct JSON
    try:
        return json.loads(raw)
    except Exception:
        pass

    # 2️⃣ Try fixing single quotes → double quotes
    try:
        fixed = raw.replace("'", '"')
        return json.loads(fixed)
    except Exception:
        pass

    # 3️⃣ Plain text alert — wrap as signal
    return {"signal": raw, "symbol": "NIFTY", "price": "0"}

# =========================
# WEBHOOK
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():

    global last_signal, last_signal_time

    try:

        # =========================
        # RAW DATA
        # =========================

        raw_data = request.data.decode("utf-8").strip()

        if not raw_data:
            print("⚠️ Empty payload received")
            return jsonify({"status": "empty"}), 200

        print("\n==============================")
        print("📩 NEW WEBHOOK RECEIVED")
        print("==============================")
        print(raw_data)

        # =========================
        # SAFE JSON PARSE
        # =========================

        data = safe_parse(raw_data)

        # =========================
        # FIELDS
        # =========================

        signal      = str(data.get("signal", "SIGNAL")).strip()
        symbol      = str(data.get("symbol", "NIFTY")).strip()
        price_raw   = data.get("price", "0")
        strike_raw  = data.get("strike", "0")
        entry_raw   = data.get("entry", "0")
        sl_raw      = data.get("sl", "0")
        target_raw  = data.get("target", "0")
        timeframe   = str(data.get("timeframe", str(data.get("tf", "5")))).strip()
        time_str    = str(data.get("time", datetime.now().strftime("%H:%M"))).strip()

        def safe_float(val, default=0.0):
            try:
                return float(str(val).replace(",", "").strip())
            except:
                return default

        price  = safe_float(price_raw)
        strike = int(safe_float(strike_raw))
        entry  = safe_float(entry_raw)
        sl     = safe_float(sl_raw)
        target = safe_float(target_raw)

        # =========================
        # DUPLICATE FILTER (5 sec window)
        # =========================

        current_key = f"{signal}_{symbol}_{strike}"
        now = time.time()

        if current_key == last_signal and (now - last_signal_time) < 5:
            print("⚠️ DUPLICATE BLOCKED")
            return jsonify({"status": "duplicate"}), 200

        last_signal = current_key
        last_signal_time = now

        # =========================
        # OPTION TYPE
        # =========================

        signal_upper = signal.upper()
        option_type = "CE"

        if any(k in signal_upper for k in ["SELL", "SHORT", "BEAR", "PE", "PUT", "SUPPLY", "HEDGE", "BREAKDOWN"]):
            option_type = "PE"
        elif any(k in signal_upper for k in ["BUY", "BULL", "BREAKOUT", "DEMAND", "CE", "CALL"]):
            option_type = "CE"

        # =========================
        # MARKET DETECTION
        # =========================

        symbol_upper = symbol.upper()

        if "BANKNIFTY" in symbol_upper:
            market_type = "BANKNIFTY"
        elif "FINNIFTY" in symbol_upper:
            market_type = "FINNIFTY"
        elif "SENSEX" in symbol_upper:
            market_type = "SENSEX"
        elif "CRUDE" in symbol_upper:
            market_type = "CRUDEOIL"
        elif "NIFTY" in symbol_upper:
            market_type = "NIFTY"
        else:
            market_type = symbol_upper

        # =========================
        # TRADING SYMBOL
        # =========================

        if strike > 0:
            trading_symbol = f"{market_type} {strike} {option_type}"
        else:
            trading_symbol = f"{market_type} {option_type}"

        # =========================
        # DISCLAIMER
        # =========================

        disclaimer = "Commodity market is risky." if "CRUDE" in market_type else "Equity market is risky."

        # =========================
        # TELEGRAM MESSAGE
        # =========================

        lines = [f"🚨 <b>{signal}</b>", ""]

        lines.append(f"🌍 Market : {market_type}")

        if strike > 0:
            lines.append(f"🎯 Strike : {strike}")

        lines.append(f"📈 Symbol : {trading_symbol}")
        lines.append(f"🕒 TF : {timeframe}")
        lines.append("")

        if entry > 0:
            lines.append(f"📈 Entry : {round(entry, 1)}")
        if sl > 0:
            lines.append(f"🛑 SL : {round(sl, 1)}")
        if target > 0:
            lines.append(f"🎯 Target : {round(target, 1)}")
        if price > 0:
            lines.append(f"💰 Live Price : {round(price, 1)}")

        lines.append(f"⏰ Time : {time_str}")
        lines.append("")
        lines.append(f"⚠️ {disclaimer}")
        lines.append("Trade at your own risk.")

        telegram_message = "\n".join(lines)

        # =========================
        # SEND (BACKGROUND THREAD)
        # =========================

        Thread(target=send_telegram_message, args=(telegram_message,), daemon=True).start()

        print(f"✅ Signal processed: {signal} | {market_type} | {strike}")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"\n❌ WEBHOOK ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
