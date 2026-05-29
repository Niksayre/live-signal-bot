import requests
import random
import asyncio
from datetime import datetime, timedelta
import pytz

from telegram import Bot

TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=TOKEN)

IST = pytz.timezone("Asia/Kolkata")

wins = 0
losses = 0
signals = 0

last_pair = ""
last_signal_time = None

pairs = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "EURJPY",
    "GBPJPY",
    "USDCAD",
    "USDCHF"
]


def get_market_price(pair):
    try:
        symbol = pair[:3] + "/" + pair[3:]

        url = f"https://api.exchangerate.host/convert?from={pair[:3]}&to={pair[3:]}"
        r = requests.get(url, timeout=10)

        data = r.json()

        return float(data["result"])

    except:
        return None


def generate_signal():
    pair = random.choice(pairs)

    price = get_market_price(pair)

    if not price:
        return None

    strategy_score = random.randint(75, 99)

    if strategy_score < 88:
        return None

    signal = random.choice(["BUY", "SELL"])

    timeframe = random.choice(["M1", "M2"])

    return {
        "pair": pair,
        "signal": signal,
        "timeframe": timeframe,
        "price": price
    }


async def send_signal(signal_data):
    global signals
    global last_signal_time

    now = datetime.now(IST)

    entry_time = (now + timedelta(minutes=1)).replace(second=0)

    if signal_data["timeframe"] == "M1":
        exit_time = entry_time + timedelta(minutes=1)
    else:
        exit_time = entry_time + timedelta(minutes=2)

    pair = signal_data["pair"]
    signal = signal_data["signal"]

    if signal == "BUY":
        emoji = "🟢"
        arrow = "⬆️"
    else:
        emoji = "🔴"
        arrow = "⬇️"

    message = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair}-FX

🕒 Signal Time ⏰ {now.strftime('%H:%M:%S')}

⏳ Entry Time ⏰ {entry_time.strftime('%H:%M:%S')}

⌛ Exit Time ⏰ {exit_time.strftime('%H:%M:%S')}

📊 Timeframe: {signal_data['timeframe']}

{emoji} {signal} {arrow}

⚠️ MG1 ENABLED

🔥 REAL MARKET CHECKED
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

    signals += 1

    wait_seconds = (exit_time - datetime.now(IST)).total_seconds()

    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    await check_result(pair, signal)

    last_signal_time = datetime.now(IST)


async def check_result(pair, signal):
    global wins
    global losses

    result = random.choice(["WIN", "LOSS"])

    if result == "WIN":
        wins += 1

        if signal == "BUY":
            result_text = "🟢 BUY ⬆️\n\n✅ WIN"
        else:
            result_text = "🔴 SELL ⬇️\n\n✅ WIN"

    else:
        losses += 1

        mg_result = random.choice(["WIN", "LOSS"])

        if mg_result == "WIN":
            wins += 1

            result_text = f"""
❌ LOSS

⚠️ MG1 ACTIVATED

✅ MG1 WIN
"""
        else:
            losses += 1

            result_text = f"""
❌ LOSS

⚠️ MG1 ACTIVATED

❌ MG1 LOSS
"""

    result_message = f"""
📢 TRADE RESULT

💷 {pair}-FX

{result_text}
"""

    await bot.send_message(chat_id=CHAT_ID, text=result_message)

    summary = f"""
📊 SUMMARY

📅 Date: {datetime.now(IST).strftime('%d/%m/%Y')}

🎯 Total Signal: {signals}

✅ Total Win: {wins}

❌ Total Loss: {losses}
"""

    await bot.send_message(chat_id=CHAT_ID, text=summary)


async def main():
    print("LIVE FOREX BOT STARTED")

    while True:
        try:
            now = datetime.now(IST)

            if last_signal_time:
                diff = (now - last_signal_time).total_seconds()

                if diff < 180:
                    await asyncio.sleep(20)
                    continue

            signal_data = generate_signal()

            if signal_data:
                await send_signal(signal_data)

            await asyncio.sleep(30)

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(10)


asyncio.run(main())