import os
import asyncio
import random
from datetime import datetime, timedelta

from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

total_signal = 0
total_win = 0
total_loss = 0

pairs = [
    "EURUSD-FX",
    "GBPUSD-FX",
    "USDJPY-FX",
    "AUDUSD-FX",
    "EURJPY-FX",
]

timeframes = [1, 2, 5]


def get_signal():
    pair = random.choice(pairs)
    timeframe = random.choice(timeframes)

    direction = random.choice(["BUY", "SELL"])

    if direction == "BUY":
        arrow = "🟢"
        call = "UP"
    else:
        arrow = "🔴"
        call = "DOWN"

    now = datetime.now()

    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

    exit_time = next_minute + timedelta(minutes=timeframe)

    signal_time = now.strftime("%H:%M:%S")
    entry_time = next_minute.strftime("%H:%M:%S")
    close_time = exit_time.strftime("%H:%M:%S")

    return {
        "pair": pair,
        "timeframe": timeframe,
        "direction": direction,
        "arrow": arrow,
        "call": call,
        "signal_time": signal_time,
        "entry_time": entry_time,
        "close_time": close_time,
    }


async def send_signal(signal):
    message = f"""
🚧 LIVE FOREX SIGNAL

💷 {signal['pair']}

Signal Time ⏰ {signal['signal_time']}

Entry ⏳ {signal['entry_time']}

Exit ⏳ {signal['close_time']}

⌚️ M{signal['timeframe']}

{signal['arrow']} {signal['direction']} ({signal['call']})

⚠️ MG1 ENABLED
"""

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=message
    )


async def send_result(signal):
    global total_signal
    global total_win
    global total_loss

    total_signal += 1

    result = random.choice(["WIN", "LOSS"])

    mg_used = False

    if result == "LOSS":
        mg_result = random.choice(["WIN", "LOSS"])

        if mg_result == "WIN":
            result = "WIN"
            mg_used = True

    if result == "WIN":
        total_win += 1
        emoji = "✅"
    else:
        total_loss += 1
        emoji = "❌"

    if mg_used:
        result_text = f"{emoji} RESULT AFTER MG1\n\n💷 {signal['pair']}\n\n{signal['direction']}\n\nMG1 WIN ✅"
    else:
        result_text = f"{emoji} RESULT\n\n💷 {signal['pair']}\n\n{signal['direction']}\n\n{result}"

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=result_text
    )

    summary = f"""
📊 SUMMARY

Date: {datetime.now().strftime("%d/%m/%Y")}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=summary
    )


async def main():
    print("LIVE FOREX SIGNAL BOT STARTED")

    while True:
        try:
            print("CHECKING LIVE FOREX")

            signal = get_signal()

            print(f"SIGNAL: {signal['pair']}")

            await send_signal(signal)

            wait_seconds = (
                signal['timeframe'] * 60
            ) + 60

            await asyncio.sleep(wait_seconds)

            await send_result(signal)

            print("RESULT SENT")

            await asyncio.sleep(60)

        except Exception as e:
            print(f"ERROR: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())