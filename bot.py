import requests
import asyncio
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
# INDIA TIME
# ==========================================

IST = pytz.timezone("Asia/Kolkata")

# ==========================================
# MARKET PAIRS
# ==========================================

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY",
    "GBP/JPY"
]

# ==========================================
# STATISTICS
# ==========================================

total_signal = 0
total_win = 0
total_loss = 0

# ==========================================
# GET REAL PRICE
# ==========================================

def get_price(symbol):

    try:

        url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey=edf95432c6e84ca98d8f2a8c900e7e05"

        response = requests.get(url, timeout=10)

        data = response.json()

        return float(data["price"])

    except Exception as e:

        print("PRICE ERROR:", e)

        return None

# ==========================================
# STRONG SIGNAL LOGIC
# ==========================================

def generate_signal():

    pair = random.choice(pairs)

    price1 = get_price(pair)

    if not price1:
        return None

    import time
    time.sleep(2)

    price2 = get_price(pair)

    if not price2:
        return None

    difference = abs(price2 - price1)

    # weak movement ignore
    if difference < 0.00010:
        return None

    if price2 > price1:
        signal = "BUY"
    else:
        signal = "SELL"

    return {
        "pair": pair,
        "signal": signal,
        "start_price": price2
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
# CHECK RESULT
# ==========================================

def check_result(signal_type, start_price, end_price):

    if signal_type == "BUY":

        if end_price > start_price:
            return "WIN"
        else:
            return "LOSS"

    else:

        if end_price < start_price:
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

            # WAIT FOR NEW MINUTE
            if now.second != 0:
                await asyncio.sleep(1)
                continue

            # =====================================
            # FIND STRONG SIGNAL
            # =====================================

            signal_data = generate_signal()

            if not signal_data:

                print("NO STRONG SETUP")

                await asyncio.sleep(60)
                continue

            pair = signal_data["pair"]
            signal = signal_data["signal"]

            entry_time = now + timedelta(minutes=1)
            exit_time = entry_time + timedelta(minutes=1)

            entry_time_str = entry_time.strftime("%H:%M:%S")
            exit_time_str = exit_time.strftime("%H:%M:%S")

            total_signal += 1

            # =====================================
            # SIGNAL DESIGN
            # =====================================

            if signal == "BUY":

                signal_text = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}</b>

🕒 Signal Time: {now.strftime('%H:%M:%S')}

⏳ Entry Time: {entry_time_str}

⌛ Exit Time: {exit_time_str}

📊 Timeframe: M1

🟢 <b>BUY ⬆️ UP</b>

⚠️ MG1 ENABLED

🔥 REAL MARKET CHECK
"""

            else:

                signal_text = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}</b>

🕒 Signal Time: {now.strftime('%H:%M:%S')}

⏳ Entry Time: {entry_time_str}

⌛ Exit Time: {exit_time_str}

📊 Timeframe: M1

🔴 <b>SELL ⬇️ DOWN</b>

⚠️ MG1 ENABLED

🔥 REAL MARKET CHECK
"""

            # =====================================
            # SEND SIGNAL
            # =====================================

            await send_message(signal_text)

            # =====================================
            # WAIT ENTRY
            # =====================================

            wait_entry = (entry_time - datetime.now(IST)).total_seconds()

            if wait_entry > 0:
                await asyncio.sleep(wait_entry)

            start_price = get_price(pair)

            if not start_price:
                continue

            # =====================================
            # WAIT EXIT
            # =====================================

            wait_exit = (exit_time - datetime.now(IST)).total_seconds()

            if wait_exit > 0:
                await asyncio.sleep(wait_exit)

            end_price = get_price(pair)

            if not end_price:
                continue

            result = check_result(signal, start_price, end_price)

            mg_used = False

            # =====================================
            # MG1
            # =====================================

            if result == "LOSS":

                mg_used = True

                mg_exit = datetime.now(IST) + timedelta(minutes=1)

                await asyncio.sleep(60)

                mg_price = get_price(pair)

                if mg_price:

                    result = check_result(signal, start_price, mg_price)

            # =====================================
            # RESULT
            # =====================================

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

            if mg_used:
                result_text += "\n⚠️ MG1 USED"

            await send_message(result_text)

            # =====================================
            # WINRATE
            # =====================================

            if total_signal > 0:

                winrate = round((total_win / total_signal) * 100, 2)

            else:

                winrate = 0

            # =====================================
            # SUMMARY
            # =====================================

            summary = f"""
📊 <b>SUMMARY</b>

📅 Date: {datetime.now(IST).strftime('%d/%m/%Y')}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}

📈 Winrate: {winrate}%
"""

            await send_message(summary)

            # =====================================
            # 1 MIN BREAK
            # =====================================

            await asyncio.sleep(60)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(10)

# ==========================================
# START
# ==========================================

asyncio.run(main())
