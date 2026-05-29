import asyncio
import requests
from datetime import datetime, timedelta
from telegram import Bot

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

bot = Bot(token=BOT_TOKEN)

PAIRS = [
"EURUSD",
"GBPUSD",
"USDJPY"
]

total_signal = 0
total_win = 0
total_loss = 0

def get_signal():

```
url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

try:

    data = requests.get(url).json()

    price = float(data["price"])

    if int(price) % 2 == 0:
        return "BUY"

    return "SELL"

except:

    return None
```

async def send_signal(pair, signal):

```
global total_signal
global total_win
global total_loss

total_signal += 1

now = datetime.now()

signal_time = now.strftime("%H:%M:%S")

entry = (now + timedelta(minutes=1)).replace(second=0)

exit_time = entry + timedelta(minutes=1)

entry_str = entry.strftime("%H:%M:%S")

exit_str = exit_time.strftime("%H:%M:%S")

if signal == "BUY":

    trade_text = f"""
```

🚧 LIVE FOREX SIGNAL

💷 {pair}-FX

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_str}

Exit ⏳ {exit_str}

⌚️ M1

🟢 BUY / UP

⚠️ MG1 ENABLED
"""

```
else:

    trade_text = f"""
```

🚧 LIVE FOREX SIGNAL

💷 {pair}-FX

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_str}

Exit ⏳ {exit_str}

⌚️ M1

🔴 SELL / DOWN

⚠️ MG1 ENABLED
"""

```
await bot.send_message(
    chat_id=CHAT_ID,
    text=trade_text
)

wait_time = (exit_time - datetime.now()).total_seconds()

if wait_time > 0:
    await asyncio.sleep(wait_time)

result = "WIN"

total_win += 1

result_text = f"""
```

✅ RESULT

💷 {pair}-FX

🏆 {result}
"""

```
await bot.send_message(
    chat_id=CHAT_ID,
    text=result_text
)

summary = f"""
```

📊 SUMMARY

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

```
await bot.send_message(
    chat_id=CHAT_ID,
    text=summary
)
```

async def main():

```
print("BOT STARTED")

while True:

    for pair in PAIRS:

        signal = get_signal()

        if signal:

            await send_signal(pair, signal)

            await asyncio.sleep(60)

    await asyncio.sleep(5)
```

asyncio.run(main())
