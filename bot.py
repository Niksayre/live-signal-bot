import os
import asyncio
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from telegram import Bot

# =========================
# TELEGRAM CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

# =========================
# INDIA TIME
# =========================

IST = ZoneInfo("Asia/Kolkata")

# =========================
# MARKET PAIRS
# =========================

PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "EURJPY",
    "AUDUSD",
    "USDCHF",
]

TIMEFRAMES = [1, 2, 5]

# =========================
# STATS
# =========================

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET LIVE FOREX PRICE
# =========================

def get_price(symbol):
    try:
        pair = symbol.lower()

        url = f"https://api.exchangerate.host/live?source={pair[:3]}"

        response = requests.get(url, timeout=10)
        data = response.json()

        quote = pair[3:].upper()

        if "quotes" in data:
            key = pair[:3].upper() + quote

            if key in data["quotes"]:
                return float(data["quotes"][key])

        return None

    except:
        return None

# =========================
# SIGNAL GENERATOR
# =========================

def generate_signal():

    pair = random.choice(PAIRS)

    direction = random.choice(["BUY", "SELL"])

    timeframe = random.choice(TIMEFRAMES)

    return pair, direction, timeframe

# =========================
# SEND TELEGRAM MESSAGE
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
# CHECK RESULT
# =========================

def check_result(direction, open_price, close_price):

    if direction == "BUY":

        if close_price > open_price:
            return "WIN"
        else:
            return "LOSS"

    else:

        if close_price < open_price:
            return "WIN"
        else:
            return "LOSS"

# =========================
# MAIN BOT
# =========================

async def run_bot():

    global total_signal
    global total_win
    global total_loss

    print("LIVE FOREX SIGNAL BOT STARTED")

    while True:

        try:

            print("CHECKING LIVE FOREX")

            now = datetime.now(IST)

            next_minute = (now + timedelta(minutes=1)).replace(
                second=0,
                microsecond=0
            )

            pair, direction, timeframe = generate_signal()

            signal_time = now.strftime("%H:%M:%S")

            entry_time = next_minute.strftime("%H:%M:%S")

            exit_dt = next_minute + timedelta(minutes=timeframe)

            exit_time = exit_dt.strftime("%H:%M:%S")

            arrow = "⬆️" if direction == "BUY" else "⬇️"

            color = "🟢" if direction == "BUY" else "🔴"

            signal_message = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair}-FX

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_time}

⌛ Exit Time ⏰ {exit_time}

📊 Timeframe: M{timeframe}

{color} {direction} {arrow}

⚠️ MG1 ENABLED

🔥 REAL FXCM MARKET
"""

            await send_message(signal_message)

            print("SIGNAL SENT:", pair)

            wait_seconds = (next_minute - datetime.now(IST)).total_seconds()

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            open_price = get_price(pair)

            if open_price is None:
                print("PRICE ERROR")
                await asyncio.sleep(30)
                continue

            await asyncio.sleep(timeframe * 60)

            close_price = get_price(pair)

            if close_price is None:
                print("PRICE ERROR")
                await asyncio.sleep(30)
                continue

            result = check_result(
                direction,
                open_price,
                close_price
            )

            total_signal += 1

            if result == "WIN":
                total_win += 1
                result_icon = "✅ WIN"
            else:
                total_loss += 1
                result_icon = "❌ LOSS"

            result_message = f"""
📢 TRADE RESULT

💷 {pair}-FX

{color} {direction} {arrow}

{result_icon}

📈 OPEN: {open_price}

📉 CLOSE: {close_price}
"""

            await send_message(result_message)

            print("RESULT SENT")

            summary_message = f"""
📊 SUMMARY

📅 Date: {datetime.now(IST).strftime("%d/%m/%Y")}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

            await send_message(summary_message)

            print("SUMMARY SENT")

            # 1 minute break before next signal
            await asyncio.sleep(60)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(30)

# =========================
# START
# =========================

asyncio.run(run_bot())