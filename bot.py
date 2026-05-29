import os
import asyncio
from datetime import datetime, timedelta

import requests
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

total_signal = 0
total_win = 0
total_loss = 0

pairs = {
    "EURUSD=X": "EURUSD-FX",
    "GBPUSD=X": "GBPUSD-FX",
    "USDJPY=X": "USDJPY-FX",
    "AUDUSD=X": "AUDUSD-FX",
    "EURJPY=X": "EURJPY-FX"
}


def get_price(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"

    data = requests.get(url).json()

    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

    closes = [x for x in closes if x is not None]

    return closes


def calculate_signal(closes):
    if len(closes) < 20:
        return None

    ema_fast = sum(closes[-5:]) / 5
    ema_slow = sum(closes[-15:]) / 15

    last = closes[-1]
    prev = closes[-2]

    momentum = last - prev

    if ema_fast > ema_slow and momentum > 0:
        return "BUY"

    if ema_fast < ema_slow and momentum < 0:
        return "SELL"

    return None


async def send_message(text):
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )
    except Exception as e:
        print("TELEGRAM ERROR:", e)


async def process_pair(symbol, pair_name):
    global total_signal
    global total_win
    global total_loss

    try:
        closes = get_price(symbol)

        signal = calculate_signal(closes)

        if signal is None:
            return

        current_price = closes[-1]

        now = datetime.now()

        entry = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

        expiry = entry + timedelta(minutes=1)

        signal_time = now.strftime("%H:%M:%S")
        entry_time = entry.strftime("%H:%M:%S")
        exit_time = expiry.strftime("%H:%M:%S")

        if signal == "BUY":
            arrow = "🟢"
            call = "UP"
        else:
            arrow = "🔴"
            call = "DOWN"

        signal_msg = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair_name}

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_time}

Exit ⏳ {exit_time}

⌚️ M1

{arrow} {signal} ({call})

⚠️ MG1 ENABLED
"""

        await send_message(signal_msg)

        print("SIGNAL SENT:", pair_name)

        wait_seconds = (entry - now).seconds + 60

        await asyncio.sleep(wait_seconds)

        closes_after = get_price(symbol)

        final_price = closes_after[-1]

        result = "LOSS"

        mg_used = False

        if signal == "BUY" and final_price > current_price:
            result = "WIN"

        elif signal == "SELL" and final_price < current_price:
            result = "WIN"

        else:
            print("TRYING MG1")

            await asyncio.sleep(60)

            closes_mg = get_price(symbol)

            mg_price = closes_mg[-1]

            if signal == "BUY" and mg_price > current_price:
                result = "MG1 WIN"
                mg_used = True

            elif signal == "SELL" and mg_price < current_price:
                result = "MG1 WIN"
                mg_used = True

        total_signal += 1

        if "WIN" in result:
            total_win += 1
            emoji = "✅"
        else:
            total_loss += 1
            emoji = "❌"

        result_msg = f"""
{emoji} RESULT

💷 {pair_name}

{signal}

{result}
"""

        await send_message(result_msg)

        summary = f"""
📊 SUMMARY

Date: {datetime.now().strftime("%d/%m/%Y")}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

        await send_message(summary)

        print("RESULT SENT:", pair_name)

    except Exception as e:
        print("PAIR ERROR:", e)


async def main():
    print("LIVE FOREX SIGNAL BOT STARTED")

    while True:
        print("CHECKING LIVE FOREX")

        for symbol, pair_name in pairs.items():
            await process_pair(symbol, pair_name)

            await asyncio.sleep(10)

        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())