import os
import time
import random
import requests
import asyncio
import pytz

from datetime import datetime, timedelta
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

IST = pytz.timezone("Asia/Kolkata")

wins = 0
losses = 0
total = 0

pairs = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "EURJPY",
    "AUDUSD",
]

timeframes = [1, 2, 5]


def get_market_price(symbol):
    try:
        url = f"https://api.exchangerate.host/live?source={symbol[:3]}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            pair = symbol[:3] + symbol[3:]

            if "quotes" in data:
                for k, v in data["quotes"].items():
                    return float(v)

        return None

    except:
        return None


def generate_signal():
    pair = random.choice(pairs)
    timeframe = random.choice(timeframes)

    signal = random.choice(["BUY", "SELL"])

    return pair, timeframe, signal


async def send_signal():
    global wins, losses, total

    pair, timeframe, signal = generate_signal()

    now = datetime.now(IST)

    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

    entry_time = next_minute
    exit_time = entry_time + timedelta(minutes=timeframe)

    signal_time = now.strftime("%H:%M:%S")
    entry_str = entry_time.strftime("%H:%M:%S")
    exit_str = exit_time.strftime("%H:%M:%S")

    message = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair}-FX

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_str}

Exit ⏳ {exit_str}

⌚️ M{timeframe}

🟢 {signal}

⚠️ MG1 ENABLED
"""

    print(f"SIGNAL SENT: {pair}")

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=message
    )

    wait_seconds = (exit_time - datetime.now(IST)).total_seconds()

    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    result = random.choice(["WIN", "LOSS"])

    if result == "WIN":
        wins += 1
    else:
        losses += 1

    total += 1

    result_message = f"""
✅ RESULT

💷 {pair}-FX

{signal}

{result}
"""

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=result_message
    )

    summary = f"""
📊 SUMMARY

Date: {datetime.now(IST).strftime("%d/%m/%Y")}

Total Signal: {total}

Total Win: {wins}

Total Loss: {losses}
"""

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=summary
    )

    print("RESULT + SUMMARY SENT")


async def main():

    print("LIVE FOREX SIGNAL BOT STARTED")

    while True:

        try:

            print("CHECKING LIVE FOREX")

            await send_signal()

            await asyncio.sleep(20)

        except Exception as e:

            print("ERROR:", e)

            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())