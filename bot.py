import requests
import asyncio
import random
from datetime import datetime, timedelta
import pytz

from telegram import Bot

# =========================
# TELEGRAM SETTINGS
# =========================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# =========================
# INDIA TIME
# =========================

IST = pytz.timezone("Asia/Kolkata")

# =========================
# PAIRS
# =========================

pairs = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "EURJPY",
    "AUDUSD",
    "USDCAD",
]

# =========================
# STATS
# =========================

total_signal = 0
total_win = 0
total_loss = 0

last_trade_time = None

# =========================
# GET MARKET PRICE
# =========================

def get_price(pair):

    try:

        symbol = pair + "=X"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"

        r = requests.get(url, timeout=10)

        data = r.json()

        close_prices = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

        return close_prices[-5:]

    except:
        return None

# =========================
# SIGNAL LOGIC
# =========================

def generate_signal():

    global last_trade_time

    pair = random.choice(pairs)

    prices = get_price(pair)

    if not prices:
        return None

    if None in prices:
        return None

    diff = prices[-1] - prices[-2]

    if abs(diff) < 0.0001:
        return None

    direction = "BUY" if diff > 0 else "SELL"

    now = datetime.now(IST)

    if last_trade_time:
        if (now - last_trade_time).seconds < 120:
            return None

    signal_time = now

    entry_time = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

    expiry_time = entry_time + timedelta(minutes=1)

    last_trade_time = now

    return {
        "pair": pair,
        "direction": direction,
        "signal_time": signal_time,
        "entry_time": entry_time,
        "expiry_time": expiry_time
    }

# =========================
# CHECK RESULT
# =========================

def check_result(pair, direction):

    prices = get_price(pair)

    if not prices:
        return "LOSS"

    open_price = prices[-2]
    close_price = prices[-1]

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
# SEND SIGNAL
# =========================

async def send_signal(signal):

    pair = signal["pair"]

    direction = signal["direction"]

    signal_time = signal["signal_time"].strftime("%H:%M:%S")

    entry_time = signal["entry_time"].strftime("%H:%M:%S")

    expiry_time = signal["expiry_time"].strftime("%H:%M:%S")

    arrow = "⬆️" if direction == "BUY" else "⬇️"

    color = "🟢" if direction == "BUY" else "🔴"

    tf = "M1"

    msg = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💱 <b>{pair}-FX</b>

🕒 Signal Time: {signal_time}

⏳ Entry Time: {entry_time}

⌛ Exit Time: {expiry_time}

📊 Timeframe: {tf}

{color} <b>{direction}</b> {arrow}

⚠️ MG1 ENABLED

🔥 REAL MARKET ANALYSIS
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="HTML"
    )

# =========================
# SEND RESULT
# =========================

async def send_result(signal, result):

    global total_signal
    global total_win
    global total_loss

    pair = signal["pair"]

    direction = signal["direction"]

    arrow = "⬆️" if direction == "BUY" else "⬇️"

    color = "🟢" if direction == "BUY" else "🔴"

    total_signal += 1

    if result == "WIN":
        total_win += 1
        result_icon = "✅ WIN"
    else:
        total_loss += 1
        result_icon = "❌ LOSS"

    date = datetime.now(IST).strftime("%d/%m/%Y")

    summary = f"""
📊 <b>SUMMARY</b>

📅 Date: {date}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

    msg = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair}-FX</b>

{color} <b>{direction}</b> {arrow}

{result_icon}
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="HTML"
    )

    await bot.send_message(
        chat_id=CHAT_ID,
        text=summary,
        parse_mode="HTML"
    )

# =========================
# MAIN LOOP
# =========================

async def main():

    print("LIVE FOREX BOT STARTED")

    while True:

        try:

            signal = generate_signal()

            if signal:

                await send_signal(signal)

                now = datetime.now(IST)

                wait_seconds = (
                    signal["expiry_time"] - now
                ).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                result = check_result(
                    signal["pair"],
                    signal["direction"]
                )

                await send_result(signal, result)

                await asyncio.sleep(60)

            else:

                await asyncio.sleep(20)

        except Exception as e:

            print("ERROR:", e)

            await asyncio.sleep(30)

# =========================
# START
# =========================

asyncio.run(main())
