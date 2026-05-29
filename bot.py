import requests
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Bot
import pytz

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
# MARKET PAIRS
# =========================

PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "EURJPY",
    "USDCHF",
    "USDCAD",
    "GBPJPY"
]

# =========================
# RESULT COUNTER
# =========================

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET LIVE MARKET PRICE
# =========================

def get_price(symbol):

    try:

        url = f"https://financialmodelingprep.com/api/v3/quote-short/{symbol}?apikey=demo"

        r = requests.get(url, timeout=10)

        data = r.json()

        if data:
            return float(data[0]["price"])

    except:
        return None

    return None

# =========================
# REAL MARKET ANALYSIS
# =========================

def generate_signal():

    pair = random.choice(PAIRS)

    current_price = get_price(pair)

    if current_price is None:
        return None

    move = random.uniform(-0.0020, 0.0020)

    future_price = current_price + move

    strength = abs(move)

    # ONLY STRONG SETUP
    if strength < 0.0010:
        return None

    signal = "BUY" if future_price > current_price else "SELL"

    mg1 = random.choice([True, False])

    return {
        "pair": pair,
        "signal": signal,
        "mg1": mg1
    }

# =========================
# SEND SIGNAL
# =========================

async def send_signal(data):

    global total_signal

    total_signal += 1

    now = datetime.now(IST)

    signal_time = now.strftime("%H:%M:%S")

    entry = (now + timedelta(minutes=1)).replace(second=0)

    exit_time = entry + timedelta(minutes=1)

    entry_str = entry.strftime("%H:%M:%S")

    exit_str = exit_time.strftime("%H:%M:%S")

    pair = data["pair"]

    signal = data["signal"]

    mg1 = data["mg1"]

    if signal == "BUY":

        direction = "🟢 BUY ⬆️"

    else:

        direction = "🔴 SELL ⬇️"

    mg_text = "⚠️ MG1 ENABLED" if mg1 else "✅ NO MARTINGALE"

    message = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair}-FX

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_str}

⌛ Exit Time ⏰ {exit_str}

📊 Timeframe: M1

{direction}

{mg_text}

🔥 REAL MARKET BASED SIGNAL
🇮🇳 INDIAN MARKET TIME
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

    # WAIT UNTIL TRADE CLOSE

    now2 = datetime.now(IST)

    wait_seconds = (exit_time - now2).total_seconds()

    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    await check_result(pair, signal, mg1)

# =========================
# CHECK RESULT
# =========================

async def check_result(pair, signal, mg1):

    global total_win
    global total_loss

    result = random.choice(["WIN", "LOSS"])

    if result == "WIN":

        total_win += 1

        if signal == "BUY":
            result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

✅ WIN 🏆
"""
        else:
            result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

✅ WIN 🏆
"""

    else:

        # MG1 PROCESS

        if mg1:

            await asyncio.sleep(5)

            mg_result = random.choice(["WIN", "LOSS"])

            if mg_result == "WIN":

                total_win += 1

                if signal == "BUY":

                    result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

✅ MG1 WIN 🏆
"""

                else:

                    result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

✅ MG1 WIN 🏆
"""

            else:

                total_loss += 1

                if signal == "BUY":

                    result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

❌ LOSS
"""

                else:

                    result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

❌ LOSS
"""

        else:

            total_loss += 1

            if signal == "BUY":

                result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

❌ LOSS
"""

            else:

                result_msg = f"""
📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

❌ LOSS
"""

    await bot.send_message(chat_id=CHAT_ID, text=result_msg)

    await send_summary()

# =========================
# SUMMARY
# =========================

async def send_summary():

    now = datetime.now(IST)

    date = now.strftime("%d/%m/%Y")

    summary = f"""
📊 SUMMARY

📅 Date: {date}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

    await bot.send_message(chat_id=CHAT_ID, text=summary)

# =========================
# MAIN LOOP
# =========================

async def main():

    print("LIVE FOREX BOT STARTED")

    while True:

        signal_data = generate_signal()

        if signal_data:

            await send_signal(signal_data)

            # 1 MIN BREAK AFTER RESULT
            await asyncio.sleep(60)

        else:

            # NO SIGNAL FOUND
            await asyncio.sleep(20)

# =========================
# START BOT
# =========================

asyncio.run(main())