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
# API SETTINGS
# =========================

API_KEY = "edf95432c6e84ca98d8f2a8c900e7e05"

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY",
    "GBP/JPY"
]

# =========================
# INDIA TIME
# =========================

india = pytz.timezone("Asia/Kolkata")

# =========================
# SUMMARY
# =========================

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET REAL MARKET PRICE
# =========================

def get_price(symbol):

    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}"
        f"&interval=1min"
        f"&outputsize=3"
        f"&apikey={API_KEY}"
    )

    try:

        response = requests.get(url, timeout=10)

        data = response.json()

        values = data.get("values")

        if not values:
            return None

        return values

    except Exception as e:
        print("PRICE ERROR:", e)
        return None

# =========================
# STRONG SETUP CHECK
# =========================

def generate_signal(candles):

    close1 = float(candles[0]["close"])
    open1 = float(candles[0]["open"])

    close2 = float(candles[1]["close"])
    open2 = float(candles[1]["open"])

    body1 = abs(close1 - open1)
    body2 = abs(close2 - open2)

    # avoid weak candles
    if body1 < 0.00010:
        return None

    # BUY setup
    if close1 > open1 and close2 > open2:
        return "BUY"

    # SELL setup
    if close1 < open1 and close2 < open2:
        return "SELL"

    return None

# =========================
# SEND TELEGRAM MESSAGE
# =========================

async def send_message(text):

    try:

        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="HTML"
        )

    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# TRADE RESULT CHECK
# =========================

async def check_result(pair, signal, entry_price):

    global total_win
    global total_loss

    # wait candle close
    await asyncio.sleep(65)

    candles = get_price(pair)

    if candles is None:
        return

    close_price = float(candles[0]["close"])

    result = "LOSS"

    if signal == "BUY":

        if close_price > entry_price:
            result = "WIN"

    if signal == "SELL":

        if close_price < entry_price:
            result = "WIN"

    # ======================
    # MG1
    # ======================

    if result == "LOSS":

        await asyncio.sleep(65)

        candles = get_price(pair)

        if candles:

            mg_close = float(candles[0]["close"])

            if signal == "BUY" and mg_close > close_price:
                result = "WIN MG1"

            elif signal == "SELL" and mg_close < close_price:
                result = "WIN MG1"

    # ======================
    # UPDATE SUMMARY
    # ======================

    if "WIN" in result:
        total_win += 1
        emoji = "✅"

    else:
        total_loss += 1
        emoji = "❌"

    now = datetime.now(india)

    summary = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair}</b>

{'🟢 <b>BUY ⬆️ UP</b>' if signal == 'BUY' else '🔴 <b>SELL ⬇️ DOWN</b>'}

{emoji} <b>{result}</b>

━━━━━━━━━━━━━━━

📊 <b>SUMMARY</b>

📅 Date: {now.strftime('%d/%m/%Y')}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

    await send_message(summary)

# =========================
# MAIN BOT
# =========================

async def run_bot():

    global total_signal

    print("LIVE FOREX BOT STARTED")

    while True:

        try:

            now = datetime.now(india)

            second = now.second

            # signal only near candle close
            if second >= 50:

                pair = random.choice(pairs)

                candles = get_price(pair)

                if candles:

                    signal = generate_signal(candles)

                    if signal:

                        total_signal += 1

                        entry_time = (
                            now + timedelta(minutes=1)
                        ).replace(second=0)

                        exit_time = entry_time + timedelta(minutes=1)

                        entry_price = float(candles[0]["close"])

                        signal_text = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💱 <b>{pair}</b>

🕒 Signal Time: {now.strftime('%H:%M:%S')}

⏳ Entry Time: {entry_time.strftime('%H:%M:%S')}

⌛ Exit Time: {exit_time.strftime('%H:%M:%S')}

📊 Timeframe: M1

{'🟢 <b>BUY ⬆️ UP</b>' if signal == 'BUY' else '🔴 <b>SELL ⬇️ DOWN</b>'}

⚠️ MG1 ENABLED

🔥 REAL MARKET
"""

                        await send_message(signal_text)

                        # wait until entry candle close
                        await check_result(
                            pair,
                            signal,
                            entry_price
                        )

                        # 1 minute cooldown
                        await asyncio.sleep(60)

            await asyncio.sleep(1)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(10)

# =========================
# START
# =========================

asyncio.run(run_bot())
