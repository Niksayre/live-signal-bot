import os
import time
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
# TELEGRAM BOT
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
# SEND TELEGRAM
# =========================================

def send_message(text):

    try:

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHANNEL_ID,
                "text": text
            },
            timeout=20
        )

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================================
# GET MARKET DATA
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
# STRATEGY
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

        # CALL

        if (
            last_ema9 > last_ema21
            and last_rsi > 55
            and last_macd > 0
        ):

            return "CALL"

        # PUT

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

        pair_name = pair.replace("/", "") + "-OTC"

        now = datetime.now()

        # =====================================
        # SIGNAL 1 MIN BEFORE ENTRY
        # =====================================

        signal_time = now.strftime("%H:%M:%S")

        entry_dt = now + timedelta(minutes=1)

        entry_time = entry_dt.strftime("%H:%M:%S")

        exit_dt = entry_dt + timedelta(seconds=duration)

        exit_time = exit_dt.strftime("%H:%M:%S")

        total_signal += 1

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

        send_message(signal_message)

        print("SIGNAL SENT:", pair_name)

        # =====================================
        # WAIT EXACTLY 1 MINUTE
        # =====================================

        time.sleep(60)

        # =====================================
        # ENTRY PRICE
        # =====================================

        before_df = get_data(pair, timeframe)

        if before_df is None:
            return

        before_price = before_df["close"].iloc[-1]

        print("ENTRY PRICE:", before_price)

        # =====================================
        # WAIT TRADE DURATION
        # =====================================

        time.sleep(duration)

        # =====================================
        # EXIT PRICE
        # =====================================

        after_df = get_data(pair, timeframe)

        if after_df is None:
            return

        after_price = after_df["close"].iloc[-1]

        print("EXIT PRICE:", after_price)

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

        send_message(result_message)

        print("RESULT SENT")

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

        send_message(summary_message)

        print("SUMMARY SENT")

        # =====================================
        # WAIT BEFORE NEXT TRADE
        # =====================================

        time.sleep(10)

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
