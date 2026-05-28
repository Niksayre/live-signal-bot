import os
import asyncio
import requests
import pandas as pd

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

print("FOREX SIGNAL BOT STARTED")

IST = ZoneInfo("Asia/Kolkata")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/JPY"
]

total_signal = 0
total_win = 0
total_loss = 0

async def send_message(text):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(
            url,
            data={
                "chat_id": CHANNEL_ID,
                "text": text
            },
            timeout=20
        )

        print("MESSAGE SENT")

    except Exception as e:

        print("TELEGRAM ERROR:", e)

def get_data(symbol):

    try:

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol={symbol}"
            f"&interval=1min"
            f"&outputsize=20"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url, timeout=20)

        data = response.json()

        if "values" not in data:

            return None

        df = pd.DataFrame(data["values"])

        df = df.iloc[::-1]

        for col in ["open", "close"]:

            df[col] = df[col].astype(float)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

def generate_signal(df):

    try:

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if (
            last["close"] > last["open"]
            and last["close"] > prev["close"]
        ):

            return "BUY"

        elif (
            last["close"] < last["open"]
            and last["close"] < prev["close"]
        ):

            return "SELL"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

def check_result(entry, exitp, signal):

    if signal == "BUY":

        return "WIN" if exitp > entry else "LOSS"

    if signal == "SELL":

        return "WIN" if exitp < entry else "LOSS"

    return "LOSS"

def next_minute():

    now = datetime.now(IST)

    return (
        now.replace(second=0, microsecond=0)
        + timedelta(minutes=1)
    )

async def process_pair(pair):

    global total_signal
    global total_win
    global total_loss

    try:

        print("CHECKING:", pair)

        df = get_data(pair)

        if df is None:

            return

        signal = generate_signal(df)

        if signal is None:

            print("NO SIGNAL")

            return

        pair_name = pair.replace("/", "")

        entry_dt = next_minute()

        exit_dt = entry_dt + timedelta(minutes=1)

        signal_time = datetime.now(IST).strftime("%H:%M:%S")

        entry_time = entry_dt.strftime("%H:%M:00")

        exit_time = exit_dt.strftime("%H:%M:00")

        total_signal += 1

        signal_text = f'''
🚧 LIVE FOREX SIGNAL

💷 {pair_name}

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_time}

Exit ⏳ {exit_time}

⌚️ M1

{"🟢 BUY" if signal == "BUY" else "🔴 SELL"}

⚠️ MG1 ENABLED
'''

        await send_message(signal_text)

        print("SIGNAL SENT")

        while datetime.now(IST) < entry_dt:

            await asyncio.sleep(1)

        entry_df = get_data(pair)

        if entry_df is None:

            return

        entry_price = entry_df["close"].iloc[-1]

        await asyncio.sleep(60)

        exit_df = get_data(pair)

        if exit_df is None:

            return

        exit_price = exit_df["close"].iloc[-1]

        result = check_result(
            entry_price,
            exit_price,
            signal
        )

        if result == "WIN":

            total_win += 1

            await send_message(f'''
✅ RESULT

💷 {pair_name}

{signal}

WIN
''')

        else:

            total_loss += 1

            await send_message(f'''
❌ RESULT

💷 {pair_name}

{signal}

LOSS
''')

        await send_message(f'''
📊 SUMMARY

Date: {datetime.now(IST).strftime("%d/%m/%Y")}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
''')

        print("SUMMARY SENT")

    except Exception as e:

        print("PROCESS ERROR:", e)

async def main():

    while True:

        try:

            print("CHECKING LIVE FOREX")

            for pair in pairs:

                await process_pair(pair)

                await asyncio.sleep(10)

            await asyncio.sleep(20)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(30)

asyncio.run(main())