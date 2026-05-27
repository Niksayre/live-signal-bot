import os
import time
import asyncio
import requests
import pandas as pd

from telegram import Bot
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta

print("LIVE SIGNAL BOT STARTED")

# =========================================
# ENV VARIABLES
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

print("TOKEN LOADED")

# =========================================
# TELEGRAM
# =========================================

bot = Bot(token=BOT_TOKEN)

# =========================================
# PAIRS
# =========================================

pairs = [
    "GBP/JPY",
    "EUR/USD",
    "USD/JPY",
    "EUR/JPY"
]

# =========================================
# SUMMARY
# =========================================

total_signal = 0
total_win = 0
total_loss = 0

# =========================================
# SEND TELEGRAM MESSAGE
# =========================================

async def send_message(text):

    try:

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================================
# GET DATA
# =========================================

def get_data(symbol, timeframe):

    try:

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol={symbol}"
            f"&interval={timeframe}"
            f"&outputsize=100"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url)

        data = response.json()

        if "values" not in data:

            print("NO DATA:", symbol)

            return None

        df = pd.DataFrame(data["values"])

        df = df.iloc[::-1]

        df["close"] = df["close"].astype(float)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

# =========================================
# SIGNAL STRATEGY
# =========================================

def generate_signal(df):

    try:

        ema9 = EMAIndicator(
            close=df["close"],
            window=9
        ).ema_indicator()

        ema21 = EMAIndicator(
            close=df["close"],
            window=21
        ).ema_indicator()

        rsi = RSIIndicator(
            close=df["close"],
            window=14
        ).rsi()

        macd = MACD(
            close=df["close"]
        ).macd()

        last_ema9 = ema9.iloc[-1]
        last_ema21 = ema21.iloc[-1]
        last_rsi = rsi.iloc[-1]
        last_macd = macd.iloc[-1]

        # STRONG CALL

        if (
            last_ema9 > last_ema21
            and last_rsi > 55
            and last_macd > 0
        ):

            return "CALL"

        # STRONG PUT

        elif (
            last_ema9 < last_ema21
            and last_rsi < 45
            and last_macd < 0
        ):

            return "PUT"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

# =========================================
# CHECK RESULT
# =========================================

def check_result(before_price, after_price, signal):

    if signal == "CALL":

        if after_price > before_price:
            return "WIN"

        return "LOSS"

    elif signal == "PUT":

        if after_price < before_price:
            return "WIN"

        return "LOSS"

    return "LOSS"

# =========================================
# PROCESS TRADE
# =========================================

def process_trade(pair, timeframe, duration):

    global total_signal
    global total_win
    global total_loss

    try:

        df = get_data(pair, timeframe)

        if df is None:
            return

        signal = generate_signal(df)

        if signal is None:

            print("NO SIGNAL:", pair)

            return

        total_signal += 1

        pair_name = pair.replace("/", "") + "-OTC"

        now = datetime.now()

        signal_time = now.strftime("%H:%M")

        entry_time = (
            now + timedelta(minutes=1)
        ).strftime("%H:%M")

        exit_time = (
            now + timedelta(minutes=1, seconds=duration)
        ).strftime("%H:%M")

        # =====================================
        # SEND SIGNAL
        # =====================================

        signal_message = f"""
🚧 LIVE SIGNAL

💷 {pair_name}

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_time}
Exit ⏳ {exit_time}

⌚️ {timeframe.upper()}

{"🟢 CALL" if signal == "CALL" else "🔴 PUT"}
"""

        asyncio.run(
            send_message(signal_message)
        )

        print("SIGNAL SENT:", pair_name)

        # =====================================
        # WAIT FOR ENTRY
        # =====================================

        time.sleep(60)

        before_df = get_data(pair, timeframe)

        if before_df is None:
            return

        before_price = before_df["close"].iloc[-1]

        # =====================================
        # WAIT FOR TRADE CLOSE
        # =====================================

        time.sleep(duration)

        after_df = get_data(pair, timeframe)

        if after_df is None:
            return

        after_price = after_df["close"].iloc[-1]

        # =====================================
        # RESULT
        # =====================================

        result = check_result(
            before_price,
            after_price,
            signal
        )

        if result == "WIN":

            total_win += 1

        else:

            total_loss += 1

        # =====================================
        # SEND RESULT
        # =====================================

        result_message = f"""
✅ RESULT

💷 {pair_name}

{signal}

{result}
"""

        asyncio.run(
            send_message(result_message)
        )

        print("RESULT SENT:", pair_name)

        # =====================================
        # SEND SUMMARY
        # =====================================

        summary_message = f"""
📊 SUMMARY

Date: {datetime.now().strftime("%d/%m/%Y")}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

        asyncio.run(
            send_message(summary_message)
        )

        print("SUMMARY SENT")

        # =====================================
        # WAIT BEFORE NEXT SIGNAL
        # =====================================

        time.sleep(15)

    except Exception as e:

        print("PROCESS ERROR:", e)

# =========================================
# MAIN LOOP
# =========================================

while True:

    try:

        print("CHECKING MARKET")

        # M1

        for pair in pairs:

            process_trade(
                pair=pair,
                timeframe="1min",
                duration=60
            )

        # M2

        for pair in pairs:

            process_trade(
                pair=pair,
                timeframe="2min",
                duration=120
            )

        # M5

        for pair in pairs:

            process_trade(
                pair=pair,
                timeframe="5min",
                duration=300
            )

        time.sleep(30)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        time.sleep(20)
