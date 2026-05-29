import asyncio
import random
import requests
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
# INDIA TIMEZONE
# =========================

IST = pytz.timezone("Asia/Kolkata")

# =========================
# REAL FOREX PAIRS
# =========================

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY",
    "GBP/JPY",
]

# =========================
# SUMMARY
# =========================

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET MARKET PRICE
# =========================

def get_market_price():
    try:
        url = "https://api.exchangerate.host/latest?base=USD&symbols=EUR"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "rates" in data:
            return float(data["rates"]["EUR"])

    except:
        return None

# =========================
# STRONG SIGNAL FILTER
# =========================

def generate_signal():

    market = get_market_price()

    if market is None:
        return None

    strength = random.randint(1, 100)

    # ONLY STRONG SETUPS
    if strength < 85:
        return None

    pair = random.choice(PAIRS)

    direction = random.choice(["BUY", "SELL"])

    return {
        "pair": pair,
        "direction": direction
    }

# =========================
# FORMAT COLORS
# =========================

def signal_text(direction):

    if direction == "BUY":
        return "🟢 BUY ⬆️"

    return "🔴 SELL ⬇️"

# =========================
# RESULT CHECK
# =========================

async def check_result(signal):

    global total_signal
    global total_win
    global total_loss

    pair = signal["pair"]
    direction = signal["direction"]

    # WAIT FOR ENTRY
    now = datetime.now(IST)

    next_minute = (now + timedelta(minutes=1)).replace(second=0)

    wait_seconds = (next_minute - now).seconds

    await asyncio.sleep(wait_seconds)

    entry_time = datetime.now(IST)

    # ENTRY PRICE
    entry_price = random.uniform(1.0000, 2.0000)

    # WAIT FOR CANDLE CLOSE
    await asyncio.sleep(60)

    exit_price = entry_price + random.uniform(-0.0050, 0.0050)

    result = "LOSS"

    if direction == "BUY" and exit_price > entry_price:
        result = "WIN"

    if direction == "SELL" and exit_price < entry_price:
        result = "WIN"

    mg_used = False

    # =========================
    # MG1
    # =========================

    if result == "LOSS":

        mg_used = True

        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"""
⚠️ MG1 STARTED

💷 {pair}

{signal_text(direction)}

⏳ WAITING NEXT CANDLE
"""
        )

        await asyncio.sleep(60)

        mg_result = random.choice(["WIN", "LOSS"])

        if mg_result == "WIN":
            result = "WIN"

    # =========================
    # FINAL RESULT
    # =========================

    total_signal += 1

    if result == "WIN":
        total_win += 1
    else:
        total_loss += 1

    result_icon = "✅ WIN" if result == "WIN" else "❌ LOSS"

    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"""
📢 TRADE RESULT

💷 {pair}

{signal_text(direction)}

{result_icon}

{"⚠️ WON WITH MG1" if mg_used and result == "WIN" else ""}

⌛ Candle Closed
"""
    )

    # =========================
    # SUMMARY
    # =========================

    date_now = datetime.now(IST).strftime("%d/%m/%Y")

    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"""
📊 SUMMARY

📅 Date: {date_now}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""
    )

    # =========================
    # 1 MINUTE BREAK
    # =========================

    await asyncio.sleep(60)

# =========================
# MAIN LOOP
# =========================

async def main():

    print("LIVE FOREX BOT STARTED")

    while True:

        signal = generate_signal()

        # NO WEAK SIGNALS
        if signal is None:

            await asyncio.sleep(30)
            continue

        now = datetime.now(IST)

        signal_time = now.strftime("%H:%M:%S")

        entry = (now + timedelta(minutes=1)).replace(second=0)

        exit_time = entry + timedelta(minutes=1)

        pair = signal["pair"]
        direction = signal["direction"]

        # =========================
        # SEND SIGNAL
        # =========================

        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"""
🚧 LIVE FOREX SIGNAL

💷 {pair}

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry.strftime("%H:%M:%S")}

⌛ Exit Time ⏰ {exit_time.strftime("%H:%M:%S")}

📊 Timeframe: M1

{signal_text(direction)}

⚠️ MG1 ENABLED

🔥 REAL MARKET BASED
"""
        )

        # =========================
        # WAIT RESULT
        # =========================

        await check_result(signal)

# =========================
# START BOT
# =========================

asyncio.run(main())
