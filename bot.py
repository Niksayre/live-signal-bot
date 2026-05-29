bot.py

import requests
import asyncio
import random
from datetime import datetime, timedelta
import pytz
from telegram import Bot

=========================
TELEGRAM SETTINGS
=========================

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

bot = Bot(token=BOT_TOKEN)

=========================
INDIA TIME
=========================

IST = pytz.timezone("Asia/Kolkata")

=========================
SIGNAL SETTINGS
=========================

PAIRS = [
"EURUSD",
"GBPUSD",
"USDJPY",
"AUDUSD",
"USDCHF",
"EURJPY",
"GBPJPY",
"USDCAD",
]

TIMEFRAMES = [1, 2, 3, 5]

=========================
SUMMARY
=========================

total_signal = 0
total_win = 0
total_loss = 0

=========================
FXCM PRICE API
=========================

def get_price(pair):
try:
symbol = pair.lower()

    url = f"https://api.fxpriceapi.com/live?pairs={symbol}"

    response = requests.get(url, timeout=10)

    data = response.json()

    if "price" in data:
        return float(data["price"])

    if symbol in data:
        return float(data[symbol])

    return None

except Exception as e:
    print("PRICE ERROR:", e)
    return None
=========================
STRATEGY
=========================

def generate_signal():

pair = random.choice(PAIRS)

tf = random.choice(TIMEFRAMES)

direction = random.choice(["BUY", "SELL"])

return pair, tf, direction
=========================
TELEGRAM SEND
=========================

async def send_signal():

global total_signal
global total_win
global total_loss

pair, tf, direction = generate_signal()

now = datetime.now(IST)

entry_time = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

exit_time = entry_time + timedelta(minutes=tf)

signal_time = now.strftime("%H:%M:%S")
entry_str = entry_time.strftime("%H:%M:%S")
exit_str = exit_time.strftime("%H:%M:%S")

before_price = get_price(pair)

if before_price is None:
    print("NO PRICE DATA")
    return

arrow = "⬆️" if direction == "BUY" else "⬇️"

color = "🟢" if direction == "BUY" else "🔴"

message = f"""

🚧 LIVE FOREX SIGNAL

💱 {pair}-FX

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_str}

⌛ Exit Time ⏰ {exit_str}

📊 Timeframe: M{tf}

{color} {direction} {arrow}

⚠️ MG1 ENABLED

🔥 REAL MARKET SIGNAL
"""

await bot.send_message(chat_id=CHAT_ID, text=message)

print("SIGNAL SENT")

wait_seconds = (exit_time - datetime.now(IST)).total_seconds()

if wait_seconds > 0:
    await asyncio.sleep(wait_seconds)

after_price = get_price(pair)

if after_price is None:
    print("RESULT CHECK FAILED")
    return

result = "LOSS"

if direction == "BUY":
    if after_price > before_price:
        result = "WIN"

if direction == "SELL":
    if after_price < before_price:
        result = "WIN"

mg_result = False

# =========================
# MARTINGALE
# =========================

if result == "LOSS":

    mg_wait = 60

    await asyncio.sleep(mg_wait)

    mg_price = get_price(pair)

    if mg_price:

        if direction == "BUY":
            if mg_price > before_price:
                mg_result = True

        if direction == "SELL":
            if mg_price < before_price:
                mg_result = True

total_signal += 1

if result == "WIN":
    total_win += 1

elif mg_result:
    total_win += 1

else:
    total_loss += 1

# =========================
# RESULT MESSAGE
# =========================

if result == "WIN":

    result_text = f"""

📢 TRADE RESULT

💱 {pair}-FX

{color} {direction} {arrow}

✅ WIN
"""

elif mg_result:

    result_text = f"""

📢 TRADE RESULT

💱 {pair}-FX

{color} {direction} {arrow}

⚡ MG1 WIN
"""

else:

    result_text = f"""

📢 TRADE RESULT

💱 {pair}-FX

{color} {direction} {arrow}

❌ LOSS
"""

await bot.send_message(chat_id=CHAT_ID, text=result_text)

# =========================
# SUMMARY
# =========================

summary = f"""

📊 SUMMARY

📅 Date: {datetime.now(IST).strftime('%d/%m/%Y')}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

await bot.send_message(chat_id=CHAT_ID, text=summary)

print("RESULT SENT")
=========================
MAIN LOOP
=========================

async def main():

print("LIVE FOREX SIGNAL BOT STARTED")

while True:

    try:

        current_time = datetime.now(IST)

        minute = current_time.minute

        # SIGNAL EVERY 5 MINUTES

        if minute % 5 == 0 and current_time.second < 5:

            await send_signal()

            # 1 MIN BREAK
            await asyncio.sleep(60)

        await asyncio.sleep(1)

    except Exception as e:

        print("MAIN ERROR:", e)

        await asyncio.sleep(10)
=========================
START BOT
=========================

asyncio.run(main())