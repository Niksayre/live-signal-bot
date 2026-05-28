import os
import time
import random
import requests
import pandas as pd

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

print("REAL FOREX SIGNAL BOT STARTED")

# =========================================
# INDIA TIME
# =========================================

IST = ZoneInfo("Asia/Kolkata")

# =========================================
# ENV VARIABLES
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

# =========================================
# PAIRS
# =========================================

pairs = [
    "EUR/USD",
    "GBP/USD",
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

# =========================================
# GET FOREX DATA
# =========================================

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

# =========================================
# STRATEGY
# =========================================

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

        last_close = df["close"].iloc[-1]

        # BUY

        if (

            ema5.iloc[-1] > ema10.iloc[-1]

            and rsi.iloc[-1] > 50

        ):

            return "BUY"

        # SELL

        elif (

            ema5.iloc[-1] < ema10.iloc[-1]

            and rsi.iloc[-1] < 50

        ):

            return "SELL"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

# =========================================
# CHECK RESULT
# =========================================

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

# =========================================
# NEXT CANDLE
# =========================================

def next_candle():

    now = datetime.now(IST)

    return (
        now.replace(second=0, microsecond=0)
        + timedelta(minutes=1)
    )

# =========================================
# PROCESS TRADE
# =========================================

def process_trade(pair):

    global total_signal
    global total_win
    global total_loss

    try:

        # RANDOM TIMEFRAME
        timeframe_choice = random.choice([
            ("1min", 1),
            ("2min", 2),
            ("5min", 5)
        ])

        timeframe = timeframe_choice[0]

        duration_min = timeframe_choice[1]

        duration_sec = duration_min * 60

        print("CHECKING:", pair, timeframe)

        df = get_data(pair, timeframe)

        if df is None:

            return

        signal = generate_signal(df)

        if signal is None:

            print("NO SIGNAL")

            return

        pair_name = pair.replace("/", "")

        # TIMES

        entry_dt = next_candle()

        exit_dt = entry_dt + timedelta(
            minutes=duration_min
        )

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

⌚️ M{duration_min}

{"🟢 BUY" if signal == "BUY" else "🔴 SELL"}

⚠️ MG1 ENABLED
"""

        send_message(signal_message)

        print("SIGNAL SENT")

        # WAIT FOR ENTRY

        while datetime.now(IST) < entry_dt:

            time.sleep(1)

        # ENTRY PRICE

        entry_df = get_data(pair, timeframe)

        if entry_df is None:

            return

        entry_price = entry_df["close"].iloc[-1]

        print("ENTRY:", entry_price)

        # WAIT CANDLE CLOSE

        time.sleep(duration_sec)

        # EXIT PRICE

        exit_df = get_data(pair, timeframe)

        if exit_df is None:

            return

        exit_price = exit_df["close"].iloc[-1]

        print("EXIT:", exit_price)

        # RESULT

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

            result_message = f"""
✅ RESULT

💷 {pair_name}

{signal}

WIN
"""

            send_message(result_message)

        # =====================================
        # LOSS -> MG1
        # =====================================

        else:

            send_message(f"""
❌ LOSS

💷 {pair_name}

Applying MG1...
""")

            print("STARTING MG1")

            # MG1 ENTRY

            mg_entry_df = get_data(pair, timeframe)

            if mg_entry_df is None:

                return

            mg_entry = mg_entry_df["close"].iloc[-1]

            # WAIT NEXT CANDLE

            time.sleep(duration_sec)

            # MG1 EXIT

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

                send_message(f"""
✅ MG1 RESULT

💷 {pair_name}

{signal}

WIN
""")

            else:

                total_loss += 1

                send_message(f"""
❌ MG1 RESULT

💷 {pair_name}

{signal}

LOSS
""")

        # =====================================
        # SUMMARY
        # =====================================

        summary_message = f"""
📊 SUMMARY

Date: {datetime.now(IST).strftime("%d/%m/%Y")}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

        send_message(summary_message)

        print("SUMMARY SENT")

        # WAIT BEFORE NEXT SIGNAL

        time.sleep(20)

    except Exception as e:

        print("PROCESS ERROR:", e)

# =========================================
# MAIN LOOP
# =========================================

while True:

    try:

        print("CHECKING LIVE FOREX")

        for pair in pairs:

            process_trade(pair)

            # API SAFETY
            time.sleep(30)

        # MAIN WAIT
        time.sleep(60)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        time.sleep(60)