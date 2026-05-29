import requests
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# ==============================
# TELEGRAM SETTINGS
# ==============================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# ==============================
# API SETTINGS
# ==============================

API_KEY = "edf95432c6e84ca98d8f2a8c900e7e05"

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY",
    "GBP/JPY"
]

# ==============================
# INDIA TIME
# ==============================

IST = pytz.timezone("Asia/Kolkata")

# ==============================
# SUMMARY
# ==============================

total_signal = 0
total_win = 0
total_loss = 0

last_trade_time = None

# ==============================
# GET MARKET DATA
# ==============================

def get_candles(pair):

    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=10&apikey={API_KEY}"

    try:
        response = requests.get(url).json()

        if "values" not in response:
            print("API ERROR:", response)
            return None

        return response["values"]

    except Exception as e:
        print("PRICE ERROR:", e)
        return None

# ==============================
# SIGNAL LOGIC
# ==============================

def generate_signal(candles):

    try:

        c1 = candles[0]
        c2 = candles[1]
        c3 = candles[2]

        close1 = float(c1["close"])
        open1 = float(c1["open"])

        close2 = float(c2["close"])
        open2 = float(c2["open"])

        close3 = float(c3["close"])
        open3 = float(c3["open"])

        bullish = 0
        bearish = 0

        if close1 > open1:
            bullish += 1
        else:
            bearish += 1

        if close2 > open2:
            bullish += 1
        else:
            bearish += 1

        if close3 > open3:
            bullish += 1
        else:
            bearish += 1

        if bullish >= 3:
            return "BUY"

        if bearish >= 3:
            return "SELL"

        return None

    except:
        return None

# ==============================
# SEND SIGNAL
# ==============================

async def send_signal(pair, signal):

    now = datetime.now(IST)

    signal_time = now.strftime("%H:%M:%S")

    entry = (now + timedelta(minutes=1)).replace(second=0)
    exit_time = entry + timedelta(minutes=1)

    entry_str = entry.strftime("%H:%M:%S")
    exit_str = exit_time.strftime("%H:%M:%S")

    if signal == "BUY":

        msg = f"""
🚨 LIVE FOREX SIGNAL 🚨

💷 {pair}

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_str}

⌛ Exit Time ⏰ {exit_str}

📊 Timeframe: M1

🟢 BUY ⬆️ UP

⚠️ MG1 ENABLED

🔥 REAL MARKET
"""

    else:

        msg = f"""
🚨 LIVE FOREX SIGNAL 🚨

💷 {pair}

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_str}

⌛ Exit Time ⏰ {exit_str}

📊 Timeframe: M1

🔴 SELL ⬇️ DOWN

⚠️ MG1 ENABLED

🔥 REAL MARKET
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg
    )

    return entry, exit_time

# ==============================
# CHECK RESULT
# ==============================

async def check_result(pair, signal, entry_time, exit_time):

    global total_signal
    global total_win
    global total_loss

    # wait until candle closes
    while datetime.now(IST) < exit_time:
        await asyncio.sleep(1)

    candles = get_candles(pair)

    if candles is None:
        return

    candle = candles[0]

    open_price = float(candle["open"])
    close_price = float(candle["close"])

    result = "LOSS"

    if signal == "BUY":

        if close_price > open_price:
            result = "WIN"

    if signal == "SELL":

        if close_price < open_price:
            result = "WIN"

    # MG1
    if result == "LOSS":

        mg_wait = exit_time + timedelta(minutes=1)

        while datetime.now(IST) < mg_wait:
            await asyncio.sleep(1)

        mg_candles = get_candles(pair)

        if mg_candles:

            mg = mg_candles[0]

            mg_open = float(mg["open"])
            mg_close = float(mg["close"])

            if signal == "BUY" and mg_close > mg_open:
                result = "WIN ✅ MG1"

            elif signal == "SELL" and mg_close < mg_open:
                result = "WIN ✅ MG1"

    total_signal += 1

    if "WIN" in result:
        total_win += 1
    else:
        total_loss += 1

    # RESULT MESSAGE

    if signal == "BUY":

        result_msg = f"""
📢 TRADE RESULT

💷 {pair}

🟢 BUY ⬆️ UP

{'✅ WIN' if 'WIN' in result else '❌ LOSS'}
"""

    else:

        result_msg = f"""
📢 TRADE RESULT

💷 {pair}

🔴 SELL ⬇️ DOWN

{'✅ WIN' if 'WIN' in result else '❌ LOSS'}
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=result_msg
    )

    # WINRATE

    if total_signal > 0:
        winrate = round((total_win / total_signal) * 100, 2)
    else:
        winrate = 0

    today = datetime.now(IST).strftime("%d/%m/%Y")

    summary = f"""
📊 SUMMARY

📅 Date: {today}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}

📈 Winrate: {winrate}%
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=summary
    )

# ==============================
# MAIN BOT
# ==============================

async def run_bot():

    global last_trade_time

    print("LIVE FOREX BOT STARTED")

    while True:

        now = datetime.now(IST)

        # avoid spam
        if last_trade_time:

            diff = (now - last_trade_time).seconds

            if diff < 120:
                await asyncio.sleep(5)
                continue

        found_signal = False

        for pair in PAIRS:

            candles = get_candles(pair)

            if candles is None:
                continue

            signal = generate_signal(candles)

            if signal:

                found_signal = True

                last_trade_time = datetime.now(IST)

                entry_time, exit_time = await send_signal(pair, signal)

                await check_result(
                    pair,
                    signal,
                    entry_time,
                    exit_time
                )

                break

        if not found_signal:
            print("No strong setup found")

        await asyncio.sleep(15)

# ==============================
# START
# ==============================

asyncio.run(run_bot())
