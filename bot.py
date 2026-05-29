import requests
import time
import os
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# =========================================
# TELEGRAM + API CONFIG
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=BOT_TOKEN)

# =========================================
# TIMEZONE
# =========================================

IST = pytz.timezone("Asia/Kolkata")

# =========================================
# REAL FOREX PAIRS
# =========================================

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY",
    "GBP/JPY",
    "EUR/GBP"
]

# =========================================
# SUMMARY VARIABLES
# =========================================

total_signal = 0
total_win = 0
total_loss = 0

# =========================================
# SEND TELEGRAM MESSAGE
# =========================================

def send_message(text):

    try:

        bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="HTML"
        )

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================================
# GET REAL MARKET DATA
# =========================================

def get_candles(pair):

    try:

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={pair}"
            f"&interval=1min"
            f"&outputsize=10"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url, timeout=10)

        data = response.json()

        if "values" not in data:

            print("API ERROR:", data)

            return None

        return data["values"]

    except Exception as e:

        print("PRICE ERROR:", e)

        return None

# =========================================
# SIGNAL LOGIC
# =========================================

def generate_signal(candles):

    try:

        closes = [float(c["close"]) for c in candles]
        highs = [float(c["high"]) for c in candles]
        lows = [float(c["low"]) for c in candles]

        current = closes[0]

        resistance = max(highs[1:5])

        support = min(lows[1:5])

        momentum = closes[0] - closes[3]

        # BUY SIGNAL

        if current > resistance and momentum > 0:

            return "BUY"

        # SELL SIGNAL

        if current < support and momentum < 0:

            return "SELL"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

# =========================================
# RESULT CHECK
# =========================================

def check_result(signal, entry, close):

    if signal == "BUY":

        if close > entry:
            return "WIN"

        else:
            return "LOSS"

    if signal == "SELL":

        if close < entry:
            return "WIN"

        else:
            return "LOSS"

# =========================================
# MAIN BOT
# =========================================

print("LIVE FOREX BOT STARTED")

while True:

    try:

        signal_found = False

        for pair in PAIRS:

            candles = get_candles(pair)

            if candles is None:
                continue

            signal = generate_signal(candles)

            if signal is None:
                continue

            signal_found = True

            now = datetime.now(IST)

            signal_time = now.strftime("%H:%M:%S")

            # =====================================
            # ENTRY TIME
            # =====================================

            entry_dt = now + timedelta(minutes=1)

            exit_dt = entry_dt + timedelta(minutes=1)

            entry_time = entry_dt.strftime("%H:%M:%S")

            exit_time = exit_dt.strftime("%H:%M:%S")

            pair_name = pair.replace("/", "")

            # =====================================
            # SIGNAL MESSAGE
            # =====================================

            if signal == "BUY":

                message = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💱 <b>{pair_name}-FX</b>

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_time}

⌛ Exit Time ⏰ {exit_time}

📊 Timeframe: M1

🟢 <b>BUY ⬆️</b>

📈 Direction: <b>UP</b>

⚠️ MG1 ENABLED

🔥 REAL MARKET
"""

            else:

                message = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💱 <b>{pair_name}-FX</b>

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_time}

⌛ Exit Time ⏰ {exit_time}

📊 Timeframe: M1

🔴 <b>SELL ⬇️</b>

📉 Direction: <b>DOWN</b>

⚠️ MG1 ENABLED

🔥 REAL MARKET
"""

            send_message(message)

            total_signal += 1

            # =====================================
            # WAIT FOR ENTRY
            # =====================================

            time.sleep(60)

            entry_candle = get_candles(pair)

            if entry_candle is None:
                continue

            entry_price = float(entry_candle[0]["close"])

            # =====================================
            # WAIT FOR EXIT
            # =====================================

            time.sleep(60)

            result_candle = get_candles(pair)

            if result_candle is None:
                continue

            close_price = float(result_candle[0]["close"])

            result = check_result(
                signal,
                entry_price,
                close_price
            )

            # =====================================
            # MG1
            # =====================================

            if result == "LOSS":

                mg_entry = close_price

                time.sleep(60)

                mg_candle = get_candles(pair)

                if mg_candle:

                    mg_close = float(mg_candle[0]["close"])

                    mg_result = check_result(
                        signal,
                        mg_entry,
                        mg_close
                    )

                    if mg_result == "WIN":

                        result = "WIN (MG1)"

            # =====================================
            # SUMMARY
            # =====================================

            if "WIN" in result:

                total_win += 1

            else:

                total_loss += 1

            # =====================================
            # RESULT MESSAGE
            # =====================================

            if signal == "BUY":

                result_msg = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair_name}-FX</b>

🟢 <b>BUY ⬆️</b>

{"✅ <b>" + result + "</b>" if "WIN" in result else "❌ <b>LOSS</b>"}
"""

            else:

                result_msg = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair_name}-FX</b>

🔴 <b>SELL ⬇️</b>

{"✅ <b>" + result + "</b>" if "WIN" in result else "❌ <b>LOSS</b>"}
"""

            send_message(result_msg)

            # =====================================
            # WINRATE
            # =====================================

            winrate = round(
                (total_win / total_signal) * 100,
                2
            )

            today = datetime.now(IST).strftime("%d/%m/%Y")

            summary = f"""
📊 <b>SUMMARY</b>

📅 Date: {today}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}

🏆 Winrate: {winrate}%
"""

            send_message(summary)

            # =====================================
            # 1 MIN BREAK
            # =====================================

            time.sleep(60)

        # =========================================
        # NO SPAM
        # =========================================

        if not signal_found:

            print("No strong setup found")

            time.sleep(20)

    except Exception as e:

        print("MAIN ERROR:", e)

        time.sleep(30)
