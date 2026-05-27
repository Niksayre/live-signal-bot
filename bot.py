import os
import requests
import pandas as pd
import time

from telegram import Bot
import asyncio
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime

print("BOT STARTED SUCCESSFULLY")

# =========================================
# ENVIRONMENT VARIABLES
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

print("BOT TOKEN LOADED")
print("CHANNEL:", CHANNEL_ID)

# =========================================
# TELEGRAM BOT
# =========================================

bot = Bot(token=BOT_TOKEN)

# =========================================
# FOREX PAIRS
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
# GET LIVE MARKET DATA
# =========================================

def get_data(symbol):

    try:

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol={symbol}"
            f"&interval=1min"
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

        print("GET DATA ERROR:", e)

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

        last_ema9 = ema9.iloc[-1]
        last_ema21 = ema21.iloc[-1]
        last_rsi = rsi.iloc[-1]

        # BUY SIGNAL

        if (
            last_ema9 > last_ema21
            and last_rsi > 55
        ):

            return "CALL"

        # SELL SIGNAL

        elif (
            last_ema9 < last_ema21
            and last_rsi < 45
        ):

            return "PUT"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

# =========================================
# RESULT CHECK
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
# SEND SIGNAL
# =========================================

def send_signal(pair, signal):

    global total_signal
    global total_win
    global total_loss

    try:

        total_signal += 1

        now = datetime.now()

        entry_time = now.strftime("%H:%M")

        exit_time = datetime.fromtimestamp(
            now.timestamp() + 60
        ).strftime("%H:%M")

        pair_name = pair.replace("/", "") + "-OTC"

        # =====================================
        # SIGNAL MESSAGE
        # =====================================

        signal_message = f"""
🚧 LIVE SIGNAL

💷 {pair_name}

Entry ⏳ {entry_time}
Exit ⏳ {exit_time}

⌚️ M1

{"🟢 CALL" if signal == "CALL" else "🔴 PUT"}
"""

        bot.send_message(
            chat_id=CHANNEL_ID,
            text=signal_message
        )

        print("SIGNAL SENT:", pair_name)

        # =====================================
        # BEFORE PRICE
        # =====================================

        before_df = get_data(pair)

        if before_df is None:
            return

        before_price = before_df["close"].iloc[-1]

        # WAIT 1 MINUTE

        time.sleep(60)

        # =====================================
        # AFTER PRICE
        # =====================================

        after_df = get_data(pair)

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
        # RESULT MESSAGE
        # =====================================

        result_message = f"""
✅ RESULT

💷 {pair_name}

{signal}

{result}

📊 SUMMARY

Date: {datetime.now().strftime("%d/%m/%Y")}

Total Signal: {total_signal}
Total Win: {total_win}
Total Loss: {total_loss}
"""

        bot.send_message(
            chat_id=CHANNEL_ID,
            text=result_message
        )

        print("RESULT SENT")

    except Exception as e:

        print("SEND SIGNAL ERROR:", e)

# =========================================
# MAIN LOOP
# =========================================

while True:

    try:

        for pair in pairs:

            print("CHECKING:", pair)

            df = get_data(pair)

            if df is None:
                continue

            signal = generate_signal(df)

            if signal:

                send_signal(pair, signal)

                time.sleep(10)

            else:

                print("NO SIGNAL")

        time.sleep(30)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        time.sleep(15)
