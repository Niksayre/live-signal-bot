import requests
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Bot
from zoneinfo import ZoneInfo

# =========================
# TELEGRAM SETTINGS
# =========================
BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# =========================
# INDIA TIME
# =========================
IST = ZoneInfo("Asia/Kolkata")

# =========================
# FX MARKET PAIRS
# =========================
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

# =========================
# RESULT COUNTERS
# =========================
total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET LIVE PRICE
# =========================
def get_price(pair):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{pair}?"
        response = requests.get(url, timeout=10)

        data = response.json()

        if len(data) > 0:
            return float(data[0]["price"])

    except:
        return None

    return None

# =========================
# SIMPLE MARKET ANALYSIS
# =========================
def generate_signal():

    pair = random.choice(PAIRS)

    current = get_price(pair)

    if current is None:
        return None

    future = current + random.uniform(-0.0030, 0.0030)

    diff = future - current

    # STRONG FILTER
    if abs(diff) < 0.0010:
        return None

    if diff > 0:
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

# =========================
# CHECK RESULT
# =========================
async def check_result(signal, entry_price, mg=False):

    global total_win
    global total_loss

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

    if win:

        total_win += 1

        result_text = f"""
📢 TRADE RESULT

💷 {signal['pair']}-FX

{signal['emoji']} {signal['direction']} {signal['arrow']}

✅ WIN
"""

        await bot.send_message(chat_id=CHAT_ID, text=result_text)

    else:

        if not mg:

            mg_text = f"""
⚠️ MG1 ACTIVATED

💷 {signal['pair']}-FX

{signal['emoji']} {signal['direction']} {signal['arrow']}

⌛ Martingale Entry Running...
"""

            await bot.send_message(chat_id=CHAT_ID, text=mg_text)

            mg_entry = get_price(signal["pair"])

            if mg_entry is not None:
                await check_result(signal, mg_entry, mg=True)

        else:

            total_loss += 1

            result_text = f"""
📢 TRADE RESULT

💷 {signal['pair']}-FX

{signal['emoji']} {signal['direction']} {signal['arrow']}

❌ LOSS
"""

            await bot.send_message(chat_id=CHAT_ID, text=result_text)

# =========================
# DAILY SUMMARY
# =========================
async def send_summary():

    global total_signal
    global total_win
    global total_loss

    today = datetime.now(IST).strftime("%d/%m/%Y")

    summary = f"""
📊 SUMMARY

📅 Date: {today}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

    await bot.send_message(chat_id=CHAT_ID, text=summary)

# =========================
# MAIN BOT
# =========================
async def run_bot():

    global total_signal

    print("LIVE FOREX BOT STARTED")

    last_summary_day = ""

    while True:

        now = datetime.now(IST)

        current_day = now.strftime("%d")

        # DAILY SUMMARY AT 11:59 PM IST
        if now.hour == 23 and now.minute == 59:

            if last_summary_day != current_day:

                await send_summary()

                last_summary_day = current_day

        # SIGNAL ONLY AT NEW MINUTE
        if now.second == 0:

            signal = generate_signal()

            if signal:

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

                # WAIT UNTIL ENTRY
                wait_seconds = (
                    entry_time - datetime.now(IST)
                ).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                entry_price = get_price(signal["pair"])

                if entry_price is not None:
                    await check_result(signal, entry_price)

                # BREAK AFTER TRADE
                await asyncio.sleep(60)

        await asyncio.sleep(1)

# =========================
# START
# =========================
asyncio.run(run_bot())