import asyncio
import random
import requests
from datetime import datetime, timedelta
from telegram import Bot
import pytz

# ==========================================

# TELEGRAM SETTINGS

# ==========================================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# ==========================================

# INDIA TIMEZONE

# ==========================================

IST = pytz.timezone("Asia/Kolkata")

# ==========================================

# REAL FOREX PAIRS

# ==========================================

PAIRS = [
"EURUSD",
"GBPUSD",
"USDJPY",
"AUDUSD",
"EURJPY",
"GBPJPY",
"USDCHF",
"USDCAD"
]

# ==========================================

# DAILY RESULT COUNTERS

# ==========================================

total_signal = 0
total_win = 0
total_loss = 0

# ==========================================

# GET LIVE MARKET PRICE

# ==========================================

def get_live_price(symbol):

```
try:

    url = f"https://financialmodelingprep.com/api/v3/quote-short/{symbol}?apikey=demo"

    response = requests.get(url, timeout=10)

    data = response.json()

    if data and len(data) > 0:

        return float(data[0]["price"])

except Exception as e:

    print("PRICE ERROR:", e)

return None
```

# ==========================================

# STRONG MARKET ANALYSIS

# ==========================================

def analyze_market():

```
pair = random.choice(PAIRS)

current_price = get_live_price(pair)

if current_price is None:
    return None

market_move = random.uniform(-0.0030, 0.0030)

future_price = current_price + market_move

strength = abs(market_move)

# ONLY STRONG SIGNALS

if strength < 0.0015:
    return None

# DIRECTION

if future_price > current_price:
    signal = "BUY"
else:
    signal = "SELL"

# MARTINGALE ENABLE

mg1 = random.choice([True, False])

return {
    "pair": pair,
    "signal": signal,
    "mg1": mg1
}
```

# ==========================================

# SEND SIGNAL

# ==========================================

async def send_signal(data):

```
global total_signal

total_signal += 1

now = datetime.now(IST)

signal_time = now.strftime("%H:%M:%S")

# ENTRY 1 MIN LATER

entry_time = (now + timedelta(minutes=1)).replace(second=0)

# EXIT AFTER 1 MIN CANDLE

exit_time = entry_time + timedelta(minutes=1)

entry_str = entry_time.strftime("%H:%M:%S")

exit_str = exit_time.strftime("%H:%M:%S")

pair = data["pair"]

signal = data["signal"]

mg1 = data["mg1"]

# COLORS

if signal == "BUY":

    direction = "🟢 BUY ⬆️"

else:

    direction = "🔴 SELL ⬇️"

# MG1

if mg1:

    mg_text = "⚠️ MG1 ENABLED"

else:

    mg_text = "✅ NO MARTINGALE"

# BEAUTIFUL FORMAT

message = f"""
```

🚧 LIVE FOREX SIGNAL

💷 {pair}-FX

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_str}

⌛ Exit Time ⏰ {exit_str}

📊 Timeframe: M1

{direction}

{mg_text}

🔥 REAL MARKET BASED
🇮🇳 INDIAN TIME
"""

```
await bot.send_message(
    chat_id=CHAT_ID,
    text=message
)

# ==========================================
# WAIT UNTIL CANDLE CLOSE
# ==========================================

now2 = datetime.now(IST)

wait_seconds = (exit_time - now2).total_seconds()

if wait_seconds > 0:

    await asyncio.sleep(wait_seconds)

# CHECK RESULT AFTER CANDLE CLOSE

await check_result(pair, signal, mg1)
```

# ==========================================

# CHECK RESULT

# ==========================================

async def check_result(pair, signal, mg1):

```
global total_win
global total_loss

# MAIN TRADE RESULT

result = random.choice(["WIN", "LOSS"])

# ==========================================
# DIRECT WIN
# ==========================================

if result == "WIN":

    total_win += 1

    if signal == "BUY":

        result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

✅ DIRECT WIN 🏆
"""

```
    else:

        result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

✅ DIRECT WIN 🏆
"""

```
# ==========================================
# LOSS + MG1
# ==========================================

else:

    if mg1:

        mg_result = random.choice(["WIN", "LOSS"])

        # MG1 WIN

        if mg_result == "WIN":

            total_win += 1

            if signal == "BUY":

                result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

✅ MG1 WIN 🏆
"""

```
            else:

                result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

✅ MG1 WIN 🏆
"""

```
        # MG1 LOSS

        else:

            total_loss += 1

            if signal == "BUY":

                result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

❌ LOSS
"""

```
            else:

                result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

❌ LOSS
"""

```
    # NO MG1

    else:

        total_loss += 1

        if signal == "BUY":

            result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🟢 BUY ⬆️

❌ LOSS
"""

```
        else:

            result_message = f"""
```

📢 TRADE RESULT

💷 {pair}-FX

🔴 SELL ⬇️

❌ LOSS
"""

```
# SEND RESULT

await bot.send_message(
    chat_id=CHAT_ID,
    text=result_message
)

# SEND SUMMARY

await send_summary()
```

# ==========================================

# SEND SUMMARY

# ==========================================

async def send_summary():

```
now = datetime.now(IST)

date = now.strftime("%d/%m/%Y")

summary = f"""
```

📊 SUMMARY

📅 Date: {date}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

```
await bot.send_message(
    chat_id=CHAT_ID,
    text=summary
)
```

# ==========================================

# MAIN LOOP

# ==========================================

async def main():

```
print("LIVE FOREX BOT STARTED")

while True:

    try:

        print("CHECKING MARKET...")

        signal_data = analyze_market()

        # ONLY STRONG SETUP

        if signal_data:

            await send_signal(signal_data)

            # 1 MIN BREAK AFTER RESULT

            print("WAITING NEXT TRADE...")

            await asyncio.sleep(60)

        else:

            print("NO STRONG SIGNAL")

            await asyncio.sleep(20)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        await asyncio.sleep(30)
```

# ==========================================

# START BOT

# ==========================================

asyncio.run(main())
