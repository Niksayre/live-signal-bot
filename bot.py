<<<<<<< HEAD
import os
import asyncio
import requests
import pandas as pd

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

print("LIVE FOREX BOT STARTED")

# =====================================
# INDIA TIME
# =====================================

IST = ZoneInfo("Asia/Kolkata")

# =====================================
# TOKENS
# =====================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

# =====================================
# FOREX PAIRS
# =====================================

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/JPY"
]

# =====================================
# SUMMARY
# =====================================

total_signal = 0
total_win = 0
total_loss = 0

# =====================================
# SEND TELEGRAM
# =====================================

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

# =====================================
# GET FOREX DATA
# =====================================

def get_data(symbol, interval):

    try:

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol={symbol}"
            f"&interval={interval}"
            f"&outputsize=100"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url, timeout=20)

        data = response.json()

        if "values" not in data:

            print("NO API DATA")

            return None

        df = pd.DataFrame(data["values"])

        df = df.iloc[::-1]

        for col in ["open", "close", "high", "low"]:

            df[col] = df[col].astype(float)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

# =====================================
# SIGNAL STRATEGY
# =====================================

def generate_signal(df):

    try:

        ema5 = EMAIndicator(
            close=df["close"],
            window=5
        ).ema_indicator()

        ema10 = EMAIndicator(
            close=df["close"],
            window=10
        ).ema_indicator()

        rsi = RSIIndicator(
            close=df["close"],
            window=14
        ).rsi()

        if (

            ema5.iloc[-1] > ema10.iloc[-1]

            and rsi.iloc[-1] > 50
=======
def generate_signal(df):

    try:

        close = df["close"]

        ema3 = EMAIndicator(
            close=close,
            window=3
        ).ema_indicator()

        ema5 = EMAIndicator(
            close=close,
            window=5
        ).ema_indicator()

        rsi = RSIIndicator(
            close=close,
            window=7
        ).rsi()

        current = close.iloc[-1]

        previous = close.iloc[-2]

        # BUY SIGNAL

        if (

            ema3.iloc[-1] > ema5.iloc[-1]

            and rsi.iloc[-1] > 48

            and current > previous
>>>>>>> 2a0538935e0525c03f5c0c0684d91a08f35d26d5

        ):

            return "BUY"

<<<<<<< HEAD
        elif (

            ema5.iloc[-1] < ema10.iloc[-1]

            and rsi.iloc[-1] < 50
=======
        # SELL SIGNAL

        elif (

            ema3.iloc[-1] < ema5.iloc[-1]

            and rsi.iloc[-1] < 52

            and current < previous
>>>>>>> 2a0538935e0525c03f5c0c0684d91a08f35d26d5

        ):

            return "SELL"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None
<<<<<<< HEAD

# =====================================
# RESULT CHECK
# =====================================

def check_result(entry, exitp, signal):

    if signal == "BUY":

        if exitp > entry:
            return "WIN"
        else:
            return "LOSS"

    if signal == "SELL":

        if exitp < entry:
            return "WIN"
        else:
            return "LOSS"

    return "LOSS"

# =====================================
# NEXT MINUTE CANDLE
# =====================================

def next_candle():

    now = datetime.now(IST)

    return (
        now.replace(second=0, microsecond=0)
        + timedelta(minutes=1)
    )

# =====================================
# PROCESS SIGNAL
# =====================================

async def process_trade(pair):

    global total_signal
    global total_win
    global total_loss

    try:

        print("CHECKING:", pair)

        timeframe = "1min"

        df = get_data(pair, timeframe)

        if df is None:

            return

        signal = generate_signal(df)

        if signal is None:

            print("NO SIGNAL")

            return

        pair_name = pair.replace("/", "")

        # =====================================
        # TIMES
        # =====================================

        entry_dt = next_candle()

        exit_dt = entry_dt + timedelta(minutes=1)

        signal_time = datetime.now(IST).strftime("%H:%M:%S")

        entry_time = entry_dt.strftime("%H:%M:00")

        exit_time = exit_dt.strftime("%H:%M:00")

        total_signal += 1

        # =====================================
        # SEND SIGNAL
        # =====================================

        signal_message = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair_name}

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_time}

Exit ⏳ {exit_time}

⌚️ M1

{"🟢 BUY" if signal == "BUY" else "🔴 SELL"}

⚠️ MG1 ENABLED
"""

        await send_message(signal_message)

        print("SIGNAL SENT")

        # =====================================
        # WAIT FOR ENTRY
        # =====================================

        while datetime.now(IST) < entry_dt:

            await asyncio.sleep(1)

        # =====================================
        # ENTRY PRICE
        # =====================================

        entry_df = get_data(pair, timeframe)

        if entry_df is None:

            return

        entry_price = entry_df["close"].iloc[-1]

        print("ENTRY:", entry_price)

        # =====================================
        # WAIT CLOSE
        # =====================================

        await asyncio.sleep(60)

        # =====================================
        # EXIT PRICE
        # =====================================

        exit_df = get_data(pair, timeframe)

        if exit_df is None:

            return

        exit_price = exit_df["close"].iloc[-1]

        print("EXIT:", exit_price)

        result = check_result(
            entry_price,
            exit_price,
            signal
        )

        # =====================================
        # WIN
        # =====================================

        if result == "WIN":

            total_win += 1

            await send_message(f"""
✅ RESULT

💷 {pair_name}

{signal}

WIN
""")

            print("WIN SENT")

        # =====================================
        # LOSS → MG1
        # =====================================

        else:

            await send_message(f"""
❌ LOSS

💷 {pair_name}

Applying MG1...
""")

            print("STARTING MG1")

            mg_entry_df = get_data(pair, timeframe)

            if mg_entry_df is None:

                return

            mg_entry = mg_entry_df["close"].iloc[-1]

            await asyncio.sleep(60)

            mg_exit_df = get_data(pair, timeframe)

            if mg_exit_df is None:

                return

            mg_exit = mg_exit_df["close"].iloc[-1]

            mg_result = check_result(
                mg_entry,
                mg_exit,
                signal
            )

            if mg_result == "WIN":

                total_win += 1

                await send_message(f"""
✅ MG1 RESULT

💷 {pair_name}

{signal}

WIN
""")

            else:

                total_loss += 1

                await send_message(f"""
❌ MG1 RESULT

💷 {pair_name}

{signal}

LOSS
""")

        # =====================================
        # SUMMARY
        # =====================================

        await send_message(f"""
📊 SUMMARY

Date: {datetime.now(IST).strftime("%d/%m/%Y")}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
""")

        print("SUMMARY SENT")

    except Exception as e:

        print("PROCESS ERROR:", e)

# =====================================
# MAIN LOOP
# =====================================

async def main():

    while True:

        try:

            print("CHECKING LIVE FOREX")

            for pair in pairs:

                await process_trade(pair)

                await asyncio.sleep(15)

            await asyncio.sleep(30)

        except Exception as e:

            print("MAIN LOOP ERROR:", e)

            await asyncio.sleep(60)

# =====================================
# START BOT
# =====================================

asyncio.run(main())
=======
>>>>>>> 2a0538935e0525c03f5c0c0684d91a08f35d26d5
