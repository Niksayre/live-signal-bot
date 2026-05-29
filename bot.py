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
# TWELVEDATA API
# ==========================================

API_KEY = "edf95432c6e84ca98d8f2a8c900e7e05"

# ==========================================
# INDIA TIMEZONE
# ==========================================

IST = pytz.timezone("Asia/Kolkata")

# ==========================================
# REAL FOREX PAIRS
# ==========================================

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/JPY",
    "GBP/JPY",
    "AUD/USD",
    "USD/CAD"
]

# ==========================================
# DAILY STATS
# ==========================================

total_signal = 0
total_win = 0
total_loss = 0

# ==========================================
# GET REAL MARKET PRICE
# ==========================================

def get_price(pair):

    try:

        url = f"https://api.twelvedata.com/price?symbol={pair}&apikey={API_KEY}"

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
# STRONG SIGNAL LOGIC
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

    # ignore weak market

    if movement < 0.00010:

        return None

    if second_price > first_price:

        signal = "BUY"

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
# CHECK RESULT
# ==========================================

def check_result(signal, entry_price, exit_price):

    if signal == "BUY":

        if exit_price > entry_price:
            return "WIN"

        return "LOSS"

    else:

        if exit_price < entry_price:
            return "WIN"

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

            # wait next minute

            if now.second != 0:

                await asyncio.sleep(1)
                continue

            # ==================================
            # FIND STRONG SETUP
            # ==================================

            signal_data = generate_signal()

            if signal_data is None:

                print("NO STRONG SIGNAL")

                await asyncio.sleep(60)

                continue

            pair = signal_data["pair"]
            signal = signal_data["signal"]

            signal_time = datetime.now(IST)

            entry_time = signal_time + timedelta(minutes=1)

            exit_time = entry_time + timedelta(minutes=1)

            # ==================================
            # SIGNAL FORMAT
            # ==================================

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

🔥 REAL MARKET
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

🔥 REAL MARKET
"""

            # ==================================
            # SEND SIGNAL
            # ==================================

            await send_message(signal_text)

            total_signal += 1

            # ==================================
            # WAIT ENTRY TIME
            # ==================================

            entry_wait = (
                entry_time - datetime.now(IST)
            ).total_seconds()

            if entry_wait > 0:

                await asyncio.sleep(entry_wait)

            entry_price = get_price(pair)

            if entry_price is None:
                continue

            # ==================================
            # WAIT EXIT TIME
            # ==================================

            exit_wait = (
                exit_time - datetime.now(IST)
            ).total_seconds()

            if exit_wait > 0:

                await asyncio.sleep(exit_wait)

            exit_price = get_price(pair)

            if exit_price is None:
                continue

            # ==================================
            # CHECK RESULT
            # ==================================

            result = check_result(
                signal,
                entry_price,
                exit_price
            )

            mg1_used = False

            # ==================================
            # MG1
            # ==================================

            if result == "LOSS":

                mg1_used = True

                await asyncio.sleep(60)

                mg_price = get_price(pair)

                if mg_price:

                    result = check_result(
                        signal,
                        entry_price,
                        mg_price
                    )

            # ==================================
            # RESULT FORMAT
            # ==================================

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

            # ==================================
            # SEND RESULT
            # ==================================

            await send_message(result_text)

            # ==================================
            # WINRATE
            # ==================================

            if total_signal > 0:

                winrate = round(
                    (total_win / total_signal) * 100,
                    2
                )

            else:

                winrate = 0

            # ==================================
            # SUMMARY
            # ==================================

            summary = f"""
📊 <b>DAILY SUMMARY</b>

📅 Date: {datetime.now(IST).strftime('%d/%m/%Y')}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}

📈 Winrate: {winrate}%
"""

            await send_message(summary)

            print("WAITING NEXT SIGNAL")

            # ==================================
            # BREAK AFTER TRADE
            # ==================================

            await asyncio.sleep(60)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(10)

# ==========================================
# START BOT
# ==========================================

asyncio.run(main())
