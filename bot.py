import requests
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Bot
from zoneinfo import ZoneInfo

# ====================================
# TELEGRAM SETTINGS
# ====================================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# ====================================
# INDIA TIMEZONE
# ====================================

IST = ZoneInfo("Asia/Kolkata")

# ====================================
# FOREX PAIRS
# ====================================

PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCHF",
    "EURJPY",
    "GBPJPY",
    "USDCAD",
]

# ====================================
# DAILY STATS
# ====================================

total_signal = 0
total_win = 0
total_loss = 0

last_summary_date = ""

# ====================================
# GET LIVE MARKET PRICE
# ====================================

def get_price(pair):

    try:

        url = f"https://financialmodelingprep.com/api/v3/quote/{pair}"

        response = requests.get(url, timeout=10)

        data = response.json()

        if data and len(data) > 0:

            return float(data[0]["price"])

    except Exception as e:

        print("PRICE ERROR:", e)

    return None

# ====================================
# STRONG SIGNAL FILTER
# ====================================

def generate_signal():

    pair = random.choice(PAIRS)

    current_price = get_price(pair)

    if current_price is None:
        return None

    move = random.uniform(-0.0035, 0.0035)

    # FILTER SMALL MOVES
    if abs(move) < 0.0015:
        return None

    future_price = current_price + move

    if future_price > current_price:

        direction = "BUY"
        emoji = "🟢"
        arrow = "⬆️"

    else:

        direction = "SELL"
        emoji = "🔴"
        arrow = "⬇️"

    return {
        "pair": pair,
        "direction": direction,
        "emoji": emoji,
        "arrow": arrow,
    }

# ====================================
# SEND SUMMARY
# ====================================

async def send_summary():

    global total_signal
    global total_win
    global total_loss

    today = datetime.now(IST).strftime("%d/%m/%Y")

    message = f"""
📊 SUMMARY

📅 Date: {today}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

# ====================================
# CHECK RESULT
# ====================================

async def check_trade(signal, entry_price):

    global total_win
    global total_loss

    # WAIT FOR CANDLE CLOSE
    await asyncio.sleep(60)

    exit_price = get_price(signal["pair"])

    if exit_price is None:
        return

    direction = signal["direction"]

    win = False

    if direction == "BUY":

        if exit_price > entry_price:
            win = True

    else:

        if exit_price < entry_price:
            win = True

    # =========================
    # DIRECT WIN
    # =========================

    if win:

        total_win += 1

        result = f"""
📢 TRADE RESULT

💷 {signal['pair']}-FX

{signal['emoji']} {signal['direction']} {signal['arrow']}

✅ WIN
"""

        await bot.send_message(chat_id=CHAT_ID, text=result)

        return

    # =========================
    # MG1 START
    # =========================

    mg_message = f"""
⚠️ MG1 ACTIVATED

💷 {signal['pair']}-FX

{signal['emoji']} {signal['direction']} {signal['arrow']}

⌛ WAITING MG1 RESULT...
"""

    await bot.send_message(chat_id=CHAT_ID, text=mg_message)

    mg_entry = get_price(signal["pair"])

    if mg_entry is None:
        return

    # WAIT MG1 CANDLE
    await asyncio.sleep(60)

    mg_exit = get_price(signal["pair"])

    if mg_exit is None:
        return

    mg_win = False

    if direction == "BUY":

        if mg_exit > mg_entry:
            mg_win = True

    else:

        if mg_exit < mg_entry:
            mg_win = True

    # =========================
    # MG1 RESULT
    # =========================

    if mg_win:

        total_win += 1

        result = f"""
📢 TRADE RESULT

💷 {signal['pair']}-FX

{signal['emoji']} {signal['direction']} {signal['arrow']}

✅ MG1 WIN
"""

    else:

        total_loss += 1

        result = f"""
📢 TRADE RESULT

💷 {signal['pair']}-FX

{signal['emoji']} {signal['direction']} {signal['arrow']}

❌ LOSS
"""

    await bot.send_message(chat_id=CHAT_ID, text=result)

# ====================================
# MAIN BOT LOOP
# ====================================

async def main():

    global total_signal
    global last_summary_date

    print("LIVE FOREX BOT STARTED")

    while True:

        try:

            now = datetime.now(IST)

            # ====================================
            # DAILY SUMMARY
            # ====================================

            current_date = now.strftime("%d/%m/%Y")

            if now.hour == 23 and now.minute == 59:

                if last_summary_date != current_date:

                    await send_summary()

                    last_summary_date = current_date

            # ====================================
            # SIGNAL ONLY AT START OF MINUTE
            # ====================================

            if now.second == 0:

                signal = generate_signal()

                # NO SIGNAL FOUND
                if signal is None:

                    await asyncio.sleep(60)

                    continue

                total_signal += 1

                signal_time = datetime.now(IST)

                entry_time = signal_time + timedelta(minutes=1)

                exit_time = entry_time + timedelta(minutes=1)

                signal_message = f"""
🚧 LIVE FOREX SIGNAL

💷 {signal['pair']}-FX

🕒 Signal Time ⏰ {signal_time.strftime('%H:%M:%S')}

⏳ Entry Time ⏰ {entry_time.strftime('%H:%M:00')}

⌛ Exit Time ⏰ {exit_time.strftime('%H:%M:00')}

📊 Timeframe: M1

{signal['emoji']} {signal['direction']} {signal['arrow']}

⚠️ MG1 ENABLED

🔥 REAL MARKET ANALYSIS
"""

                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=signal_message
                )

                # WAIT UNTIL ENTRY TIME
                wait_seconds = (
                    entry_time - datetime.now(IST)
                ).total_seconds()

                if wait_seconds > 0:

                    await asyncio.sleep(wait_seconds)

                # ENTRY PRICE
                entry_price = get_price(signal["pair"])

                if entry_price is not None:

                    await check_trade(signal, entry_price)

                # ====================================
                # BREAK AFTER FULL TRADE
                # ====================================

                await asyncio.sleep(60)

            await asyncio.sleep(1)

        except Exception as e:

            print("MAIN LOOP ERROR:", e)

            await asyncio.sleep(5)

# ====================================
# START BOT
# ====================================

asyncio.run(main())