import os
import asyncio
import requests
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=BOT_TOKEN)

IST = pytz.timezone("Asia/Kolkata")

pairs = [
    ("EUR/USD", "EURUSD"),
    ("GBP/USD", "GBPUSD"),
    ("USD/JPY", "USDJPY"),
    ("EUR/JPY", "EURJPY"),
]

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET FOREX DATA
# =========================

def get_forex_data(symbol, interval="1min"):

    try:

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval={interval}"
            f"&outputsize=10"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url).json()

        if "values" not in response:
            print("API ERROR:", response)
            return None

        return response["values"]

    except Exception as e:
        print("DATA ERROR:", e)
        return None

# =========================
# SIGNAL STRATEGY
# =========================

def generate_signal(candles):

    try:

        c1 = candles[0]
        c2 = candles[1]
        c3 = candles[2]

        open1 = float(c1["open"])
        close1 = float(c1["close"])

        open2 = float(c2["open"])
        close2 = float(c2["close"])

        open3 = float(c3["open"])
        close3 = float(c3["close"])

        bullish = 0
        bearish = 0

        # candle 1
        if close1 > open1:
            bullish += 1
        else:
            bearish += 1

        # candle 2
        if close2 > open2:
            bullish += 1
        else:
            bearish += 1

        # candle 3
        if close3 > open3:
            bullish += 1
        else:
            bearish += 1

        # STRONG TREND FILTER
        diff = abs(close1 - open1)

        if diff < 0.00015:
            return None

        # BUY
        if bullish >= 2:
            return "BUY"

        # SELL
        if bearish >= 2:
            return "SELL"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

# =========================
# RESULT CHECK
# =========================

def check_result(open_price, close_price, signal):

    if signal == "BUY":

        if close_price > open_price:
            return "WIN"
        else:
            return "LOSS"

    if signal == "SELL":

        if close_price < open_price:
            return "WIN"
        else:
            return "LOSS"

    return "LOSS"

# =========================
# SEND TELEGRAM
# =========================

async def send_message(text):

    try:

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================
# MARTINGALE
# =========================

async def martingale_trade(symbol, signal):

    global total_win
    global total_loss

    try:

        mg_entry = (
            datetime.now(IST) + timedelta(minutes=1)
        ).replace(second=0, microsecond=0)

        mg_exit = mg_entry + timedelta(minutes=1)

        mg_text = f"""
⚠️ MARTINGALE 1

💷 {symbol}-FX

Entry ⏳ {mg_entry.strftime('%H:%M:%S')}

Exit ⏳ {mg_exit.strftime('%H:%M:%S')}

⌚️ M1

{"🟢 BUY" if signal == "BUY" else "🔴 SELL"}
"""

        await send_message(mg_text)

        wait_time = (
            mg_exit - datetime.now(IST)
        ).total_seconds()

        if wait_time > 0:
            await asyncio.sleep(wait_time + 2)

        candles = get_forex_data(symbol)

        if not candles:
            return

        latest = candles[0]

        open_price = float(latest["open"])
        close_price = float(latest["close"])

        result = check_result(
            open_price,
            close_price,
            signal
        )

        if result == "WIN":
            total_win += 1
        else:
            total_loss += 1

        result_text = f"""
✅ MG1 RESULT

💷 {symbol}-FX

{signal}

{result}
"""

        await send_message(result_text)

    except Exception as e:

        print("MG ERROR:", e)

# =========================
# MAIN LOOP
# =========================

async def main():

    global total_signal
    global total_win
    global total_loss

    print("LIVE FOREX SIGNAL BOT STARTED")

    while True:

        try:

            now = datetime.now(IST)

            # CHECK ONLY LAST 5 SECONDS
            if now.second < 55:
                await asyncio.sleep(1)
                continue

            print("CHECKING LIVE FOREX")

            for pair_name, symbol in pairs:

                print("CHECKING:", pair_name)

                candles = get_forex_data(symbol)

                if not candles:
                    continue

                signal = generate_signal(candles)

                if signal is None:
                    continue

                current = datetime.now(IST)

                entry_time = (
                    current + timedelta(minutes=1)
                ).replace(second=0, microsecond=0)

                exit_time = entry_time + timedelta(minutes=1)

                total_signal += 1

                signal_message = f"""
🚧 LIVE FOREX SIGNAL

💷 {symbol}-FX

Signal Time ⏰ {current.strftime('%H:%M:%S')}

Entry ⏳ {entry_time.strftime('%H:%M:%S')}

Exit ⏳ {exit_time.strftime('%H:%M:%S')}

⌚️ M1

{"🟢 BUY" if signal == "BUY" else "🔴 SELL"}

⚠️ MG1 ENABLED
"""

                await send_message(signal_message)

                print("SIGNAL SENT:", symbol)

                # WAIT FOR CANDLE CLOSE
                wait_time = (
                    exit_time - datetime.now(IST)
                ).total_seconds()

                if wait_time > 0:
                    await asyncio.sleep(wait_time + 2)

                # GET RESULT
                result_candle = get_forex_data(symbol)

                if not result_candle:
                    continue

                latest = result_candle[0]

                open_price = float(latest["open"])
                close_price = float(latest["close"])

                result = check_result(
                    open_price,
                    close_price,
                    signal
                )

                # MARTINGALE
                if result == "LOSS":

                    await martingale_trade(
                        symbol,
                        signal
                    )

                else:

                    total_win += 1

                result_message = f"""
✅ RESULT

💷 {symbol}-FX

{signal}

{result}
"""

                await send_message(result_message)

                summary_message = f"""
📊 SUMMARY

Date: {datetime.now(IST).strftime('%d/%m/%Y')}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

                await send_message(summary_message)

                print("RESULT SENT:", symbol)

                await asyncio.sleep(5)

            await asyncio.sleep(2)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(10)

# =========================
# START BOT
# =========================

asyncio.run(main())