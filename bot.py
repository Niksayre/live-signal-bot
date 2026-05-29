import requests
import time
import os
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# =========================================
# CONFIG
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=BOT_TOKEN)

# =========================================
# INDIAN TIMEZONE
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
# DAILY SUMMARY
# =========================================

total_signal = 0
total_win = 0
total_loss = 0

# =========================================
# GET REAL MARKET CANDLES
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

        candles = data["values"]

        return candles

    except Exception as e:

        print("PRICE ERROR:", e)

        return None

# =========================================
# SUPPORT RESISTANCE LOGIC
# =========================================

def generate_signal(candles):

    try:

        closes = [float(c["close"]) for c in candles]
        highs = [float(c["high"]) for c in candles]
        lows = [float(c["low"]) for c in candles]

        current = closes[0]

        resistance = max(highs[1:])
        support = min(lows[1:])

        momentum = closes[0] - closes[3]

        # =====================================
        # STRONG BUY
        # =====================================

        if current > resistance and momentum > 0:

            return "BUY"

        # =====================================
        # STRONG SELL
        # =====================================

        elif current < support and momentum < 0:

            return "SELL"

        return None

    except:

        return None

# =========================================
# CHECK RESULT
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
# MAIN BOT
# =========================================

print("LIVE FOREX BOT STARTED")

while True:

    try:

        for pair in PAIRS:

            candles = get_candles(pair)

            if candles is None:
                continue

            signal = generate_signal(candles)

            if signal is None:
                continue

            global total_signal
            global total_win
            global total_loss

            now = datetime.now(IST)

            signal_time = now.strftime("%H:%M:%S")

            # =====================================
            # ENTRY AFTER 1 MINUTE
            # =====================================

            entry_time_dt = now + timedelta(minutes=1)

            exit_time_dt = entry_time_dt + timedelta(minutes=1)

            entry_time = entry_time_dt.strftime("%H:%M:%S")

            exit_time = exit_time_dt.strftime("%H:%M:%S")

            pair_name = pair.replace("/", "")

            # =====================================
            # BUY FORMAT
            # =====================================

            if signal == "BUY":

                signal_text = f"""
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

            # =====================================
            # SELL FORMAT
            # =====================================

            else:

                signal_text = f"""
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

            send_message(signal_text)

            total_signal += 1

            # =====================================
            # WAIT FOR ENTRY
            # =====================================

            time.sleep(60)

            entry_candles = get_candles(pair)

            if entry_candles is None:
                continue

            entry_price = float(entry_candles[0]["close"])

            # =====================================
            # WAIT FOR CANDLE CLOSE
            # =====================================

            time.sleep(60)

            result_candles = get_candles(pair)

            if result_candles is None:
                continue

            close_price = float(result_candles[0]["close"])

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

                mg_candles = get_candles(pair)

                if mg_candles:

                    mg_close = float(mg_candles[0]["close"])

                    mg_result = check_result(
                        signal,
                        mg_entry,
                        mg_close
                    )

                    if mg_result == "WIN":

                        result = "WIN (MG1)"

            # =====================================
            # SUMMARY COUNTS
            # =====================================

            if "WIN" in result:
                total_win += 1

            else:
                total_loss += 1

            # =====================================
            # RESULT MESSAGE
            # =====================================

            if signal == "BUY":

                result_text = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair_name}-FX</b>

🟢 <b>BUY ⬆️</b>

{ '✅ <b>' + result + '</b>' if 'WIN' in result else '❌ <b>LOSS</b>' }
"""

            else:

                result_text = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair_name}-FX</b>

🔴 <b>SELL ⬇️</b>

{ '✅ <b>' + result + '</b>' if 'WIN' in result else '❌ <b>LOSS</b>' }
"""

            send_message(result_text)

            # =====================================
            # WINRATE
            # =====================================

            winrate = 0

            if total_signal > 0:

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
        # LOOP DELAY
        # =========================================

        time.sleep(15)

    except Exception as e:

        print("MAIN ERROR:", e)

        time.sleep(30)
