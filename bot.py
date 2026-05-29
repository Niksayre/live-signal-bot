import asyncio
import requests
import random
from datetime import datetime, timedelta
import pytz

from telegram import Bot

# ==========================================
# TELEGRAM SETTINGS
# ==========================================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# ==========================================
# API KEY
# ==========================================

API_KEY = "edf95432c6e84ca98d8f2a8c900e7e05"

# ==========================================
# INDIA TIME
# ==========================================

IST = pytz.timezone("Asia/Kolkata")

# ==========================================
# FOREX PAIRS
# ==========================================

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/JPY",
    "GBP/JPY",
    "AUD/USD",
    "USD/CAD",
]

# ==========================================
# STATS
# ==========================================

total_signal = 0
total_win = 0
total_loss = 0

# ==========================================
# GET REAL MARKET PRICE
# ==========================================

def get_price(symbol):

    try:

        url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={API_KEY}"

        response = requests.get(url, timeout=10)

        data = response.json()

        if "price" not in data:
            print("API ERROR:", data)
            return None

        return float(data["price"])

    except Exception as e:

        print("PRICE ERROR:", e)

        return None

# ==========================================
# STRONG MARKET SETUP
# ==========================================

def generate_signal():

    pair = random.choice(pairs)

    first_price = get_price(pair)

    if first_price is None:
        return None

    import time
    time.sleep(3)

    second_price = get_price(pair)

    if second_price is None:
        return None

    movement = abs(second_price - first_price)

    # Ignore weak movement
    if movement < 0.00010:
        return None

    # BUY
    if second_price > first_price:

        signal = "BUY"

    # SELL
    else:

        signal = "SELL"

    return {
        "pair": pair,
        "signal": signal
    }

# ==========================================
# SEND TELEGRAM MESSAGE
# ==========================================

async def send_message(text):

    try:

        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="HTML"
        )

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# ==========================================
# RESULT CHECK
# ==========================================

def check_result(signal_type, entry_price, exit_price):

    # BUY
    if signal_type == "BUY":

        if exit_price > entry_price:
            return "WIN"
        else:
            return "LOSS"

    # SELL
    else:

        if exit_price < entry_price:
            return "WIN"
        else:
            return "LOSS"

# ==========================================
# MAIN BOT
# ==========================================

async def main():

    global total_signal
    global total_win
    global total_loss

    print("LIVE FOREX BOT STARTED")

    while True:

        try:

            now = datetime.now(IST)

            # ==============================
            # WAIT NEW MINUTE
            # ==============================

            if now.second != 0:

                await asyncio.sleep(1)
                continue

            # ==============================
            # FIND SIGNAL
            # ==============================

            signal_data = generate_signal()

            if signal_data is None:

                print("NO STRONG SIGNAL FOUND")

                await asyncio.sleep(60)
                continue

            pair = signal_data["pair"]
            signal = signal_data["signal"]

            signal_time = datetime.now(IST)

            entry_time = signal_time + timedelta(minutes=1)

            exit_time = entry_time + timedelta(minutes=1)

            # ==============================
            # FORMAT SIGNAL
            # ==============================

            if signal == "BUY":

                signal_text = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}</b>

🕒 Signal Time: {signal_time.strftime('%H:%M:%S')}

⏳ Entry Time: {entry_time.strftime('%H:%M:%S')}

⌛ Exit Time: {exit_time.strftime('%H:%M:%S')}

📊 Timeframe: M1

🟢 <b>BUY ⬆️ UP</b>

⚠️ MG1 ENABLED

🔥 REAL MARKET CHECK
"""

            else:

                signal_text = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}</b>

🕒 Signal Time: {signal_time.strftime('%H:%M:%S')}

⏳ Entry Time: {entry_time.strftime('%H:%M:%S')}

⌛ Exit Time: {exit_time.strftime('%H:%M:%S')}

📊 Timeframe: M1

🔴 <b>SELL ⬇️ DOWN</b>

⚠️ MG1 ENABLED

🔥 REAL MARKET CHECK
"""

            # ==============================
            # SEND SIGNAL
            # ==============================

            await send_message(signal_text)

            total_signal += 1

            # ==============================
            # WAIT ENTRY TIME
            # ==============================

            wait_entry = (entry_time - datetime.now(IST)).total_seconds()

            if wait_entry > 0:

                await asyncio.sleep(wait_entry)

            entry_price = get_price(pair)

            if entry_price is None:
                continue

            # ==============================
            # WAIT EXIT TIME
            # ==============================

            wait_exit = (exit_time - datetime.now(IST)).total_seconds()

            if wait_exit > 0:

                await asyncio.sleep(wait_exit)

            exit_price = get_price(pair)

            if exit_price is None:
                continue

            # ==============================
            # CHECK RESULT
            # ==============================

            result = check_result(
                signal,
                entry_price,
                exit_price
            )

            mg1_used = False

            # ==============================
            # MG1
            # ==============================

            if result == "LOSS":

                mg1_used = True

                await asyncio.sleep(60)

                mg_exit_price = get_price(pair)

                if mg_exit_price:

                    result = check_result(
                        signal,
                        entry_price,
                        mg_exit_price
                    )

            # ==============================
            # RESULT MESSAGE
            # ==============================

            if result == "WIN":

                total_win += 1

                if signal == "BUY":

                    result_text = f"""
📢 <b>TRADE RESULT</b>

💷 <b>{pair}</b>

🟢 BUY ⬆️ UP

✅ WIN
"""

                else:

                    result_text = f"""
📢 <b>TRADE RESULT</b>

💷 <b>{pair}</b>

🔴 SELL ⬇️ DOWN

✅ WIN
"""

            else:

                total_loss += 1

                if signal == "BUY":

                    result_text = f"""
📢 <b>TRADE RESULT</b>

💷 <b>{pair}</b>

🟢 BUY ⬆️ UP

❌ LOSS
"""

                else:

                    result_text = f"""
📢 <b>TRADE RESULT</b>

💷 <b>{pair}</b>

🔴 SELL ⬇️ DOWN

❌ LOSS
"""

            if mg1_used:

                result_text += "\n⚠️ MG1 USED"

            # ==============================
            # SEND RESULT
            # ==============================

            await send_message(result_text)

            # ==============================
            # WINRATE
            # ==============================

            if total_signal > 0:

                winrate = round(
                    (total_win / total_signal) * 100,
                    2
                )

            else:

                winrate = 0

            # ==============================
            # SUMMARY
            # ==============================

            summary_text = f"""
📊 <b>DAILY SUMMARY</b>

📅 Date: {datetime.now(IST).strftime('%d/%m/%Y')}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}

📈 Winrate: {winrate}%
"""

            await send_message(summary_text)

            # ==============================
            # BREAK AFTER TRADE
            # ==============================

            print("WAITING NEXT SETUP")

            await asyncio.sleep(60)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(10)

# ==========================================
# START BOT
# ==========================================

asyncio.run(main())
