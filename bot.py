import requests
import time
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Bot

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

bot = Bot(token=BOT_TOKEN)

TIMEZONE = pytz.timezone("Asia/Kolkata")

PAIRS = [
"EURUSD",
"GBPUSD",
"USDJPY",
"EURJPY",
"AUDUSD"
]

total_signal = 0
total_win = 0
total_loss = 0

def get_forex_data(pair):

```
url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=100&apikey=demo"

try:

    response = requests.get(url).json()

    candles = response["values"]

    closes = [float(x["close"]) for x in candles]
    opens = [float(x["open"]) for x in candles]

    return opens, closes

except:

    return None
```

def ema(data, period):

```
multiplier = 2 / (period + 1)

ema_value = sum(data[:period]) / period

for price in data[period:]:

    ema_value = ((price - ema_value) * multiplier) + ema_value

return ema_value
```

def rsi(closes, period=14):

```
gains = []
losses = []

for i in range(1, len(closes)):

    diff = closes[i] - closes[i - 1]

    if diff >= 0:
        gains.append(diff)
        losses.append(0)

    else:
        gains.append(0)
        losses.append(abs(diff))

avg_gain = sum(gains[-period:]) / period
avg_loss = sum(losses[-period:]) / period

if avg_loss == 0:
    return 100

rs = avg_gain / avg_loss

return 100 - (100 / (1 + rs))
```

def generate_signal(pair):

```
data = get_forex_data(pair)

if not data:
    return None

opens, closes = data

ema20 = ema(closes, 20)
ema50 = ema(closes, 50)

current_rsi = rsi(closes)

bullish = closes[-1] > opens[-1]
bearish = closes[-1] < opens[-1]

if (
    ema20 > ema50 and
    current_rsi > 55 and
    bullish
):
    return "BUY"

if (
    ema20 < ema50 and
    current_rsi < 45 and
    bearish
):
    return "SELL"

return None
```

async def send_message(message):

```
try:

    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode="HTML"
    )

except Exception as e:

    print(e)
```

async def run_bot():

```
global total_signal
global total_win
global total_loss

print("LIVE FOREX SIGNAL BOT STARTED")

while True:

    now = datetime.now(TIMEZONE)

    if now.second == 0:

        print("CHECKING LIVE FOREX")

        for pair in PAIRS:

            signal = generate_signal(pair)

            if signal:

                total_signal += 1

                signal_time = now.strftime("%H:%M:%S")

                entry_time = (
                    now + timedelta(minutes=1)
                ).replace(second=0)

                exit_time = entry_time + timedelta(minutes=5)

                entry_str = entry_time.strftime("%H:%M:%S")

                exit_str = exit_time.strftime("%H:%M:%S")

                if signal == "BUY":

                    trade_text = f"""
```

🚧 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}-FX</b>

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_str}

Exit ⏳ {exit_str}

⌚️ <b>M5</b>

🟢 <b>BUY / UP</b>

⚠️ <b>MG1 ENABLED</b>
"""

```
                else:

                    trade_text = f"""
```

🚧 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}-FX</b>

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_str}

Exit ⏳ {exit_str}

⌚️ <b>M5</b>

🔴 <b>SELL / DOWN</b>

⚠️ <b>MG1 ENABLED</b>
"""

```
                await send_message(trade_text)

                wait_entry = (
                    entry_time - datetime.now(TIMEZONE)
                ).total_seconds()

                if wait_entry > 0:
                    await asyncio.sleep(wait_entry)

                entry_data = get_forex_data(pair)

                entry_price = entry_data[1][-1]

                wait_exit = (
                    exit_time - datetime.now(TIMEZONE)
                ).total_seconds()

                if wait_exit > 0:
                    await asyncio.sleep(wait_exit)

                exit_data = get_forex_data(pair)

                exit_price = exit_data[1][-1]

                result = "LOSS"

                if signal == "BUY" and exit_price > entry_price:
                    result = "WIN"

                if signal == "SELL" and exit_price < entry_price:
                    result = "WIN"

                if result == "WIN":
                    total_win += 1
                else:
                    total_loss += 1

                result_text = f"""
```

✅ <b>RESULT</b>

💷 <b>{pair}-FX</b>

🏆 <b>{result}</b>
"""

```
                await send_message(result_text)

                summary = f"""
```

📊 <b>SUMMARY</b>

📅 Date: {now.strftime('%d/%m/%Y')}

📈 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

```
                await send_message(summary)

                await asyncio.sleep(60)

    await asyncio.sleep(1)
```

asyncio.run(run_bot())
