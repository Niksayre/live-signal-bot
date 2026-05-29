import os
import asyncio
import requests
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=BOT_TOKEN)

IST = pytz.timezone("Asia/Kolkata")

pairs = [
    ("EUR/USD", "EURUSD"),
    ("GBP/USD", "GBPUSD"),
    ("USD/JPY", "USDJPY"),
    ("EUR/JPY", "EURJPY"),
]

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET LIVE FOREX DATA
# =========================

def get_forex_data(symbol):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=50&apikey={API_KEY}"

        response = requests.get(url).json()

        if "values" not in response:
            return None

        candles = response["values"]

        return candles

    except:
        return None

# =========================
# SIGNAL STRATEGY
# =========================

def generate_signal(candles):

    closes = [float(x["close"]) for x in candles[:10]]

    last = closes[0]
    prev = closes[1]
    prev2 = closes[2]

    # TREND
    bullish = last > prev > prev2
    bearish = last < prev < prev2

    # MOMENTUM FILTER
    strength = abs(last - prev)

    if strength < 0.0002:
        return None

    if bullish:
        return "BUY"

    if bearish:
        return "SELL"

    return None

# =========================
# CHECK RESULT
# =========================

def check_result(entry_open, close_price, signal):

    if signal == "BUY":
        return "WIN" if close_price > entry_open else "LOSS"

    if signal == "SELL":
        return "WIN" if close_price < entry_open else "LOSS"

    return "LOSS"

# =========================
# SEND TELEGRAM
# =========================

async def send_message(text):
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# MAIN LOOP
# =========================

async def main():

    global total_signal
    global total_win
    global total_loss

    print("LIVE FOREX SIGNAL BOT STARTED")

    while True:

        try:

            now = datetime.now(IST)

            # WAIT UNTIL 58th SECOND
            if now.second < 58:
                await asyncio.sleep(1)
                continue

            print("CHECKING LIVE FOREX")

            for pair_name, symbol in pairs:

                candles = get_forex_data(symbol)

                if not candles:
                    continue

                signal = generate_signal(candles)

                if signal is None:
                    continue

                current = datetime.now(IST)

                entry_time = (
                    current + timedelta(minutes=1)
                ).replace(second=0, microsecond=0)

                exit_time = entry_time + timedelta(minutes=1)

                entry_str = entry_time.strftime("%H:%M:%S")
                exit_str = exit_time.strftime("%H:%M:%S")

                total_signal += 1

                signal_text = f"""
🚧 LIVE FOREX SIGNAL

💷 {symbol}-FX

Signal Time ⏰ {current.strftime('%H:%M:%S')}

Entry ⏳ {entry_str}

Exit ⏳ {exit_str}

⌚️ M1

{"🟢 BUY" if signal == "BUY" else "🔴 SELL"}

⚠️ MG1 ENABLED
"""

                await send_message(signal_text)

                print("SIGNAL SENT:", symbol)

                # WAIT UNTIL TRADE CLOSE
                wait_seconds = (exit_time - datetime.now(IST)).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds + 2)

                # GET RESULT CANDLE
                result_data = get_forex_data(symbol)

                if not result_data:
                    continue

                latest = result_data[0]

                entry_open = float(latest["open"])
                close_price = float(latest["close"])

                result = check_result(
                    entry_open,
                    close_price,
                    signal
                )

                # MARTINGALE
                if result == "LOSS":

                    mg_signal = signal

                    mg_entry = datetime.now(IST).replace(second=0, microsecond=0)
                    mg_exit = mg_entry + timedelta(minutes=1)

                    mg_text = f"""
⚠️ MARTINGALE 1

💷 {symbol}-FX

Entry ⏳ {mg_entry.strftime('%H:%M:%S')}

Exit ⏳ {mg_exit.strftime('%H:%M:%S')}

{"🟢 BUY" if mg_signal == "BUY" else "🔴 SELL"}
"""

                    await send_message(mg_text)

                    await asyncio.sleep(62)

                    mg_data = get_forex_data(symbol)

                    latest2 = mg_data[0]

                    mg_open = float(latest2["open"])
                    mg_close = float(latest2["close"])

                    result = check_result(
                        mg_open,
                        mg_close,
                        mg_signal
                    )

                if result == "WIN":
                    total_win += 1
                else:
                    total_loss += 1

                result_text = f"""
✅ RESULT

💷 {symbol}-FX

{signal}

{result}
"""

                await send_message(result_text)

                summary_text = f"""
📊 SUMMARY

Date: {datetime.now(IST).strftime('%d/%m/%Y')}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

                await send_message(summary_text)

                print("RESULT SENT:", result)

                await asyncio.sleep(5)

            await asyncio.sleep(1)

        except Exception as e:
            print("MAIN ERROR:", e)
            await asyncio.sleep(10)

# =========================
# START
# =========================

asyncio.run(main())