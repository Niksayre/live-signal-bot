import requests
import pandas as pd
import time
import threading

from telegram import Bot
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime

# =====================================
# TELEGRAM
# =====================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

# =====================================
# API
# =====================================

API_KEY = os.getenv("API_KEY")

pairs = [
    "GBP/JPY",
    "EUR/USD",
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
# GET DATA
# =====================================

def get_data(symbol):

    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}"
        f"&interval=1min"
        f"&outputsize=100"
        f"&apikey={API_KEY}"
    )

    response = requests.get(url).json()

    values = response.get("values")

    if not values:
        return None

    df = pd.DataFrame(values)

    df = df.iloc[::-1]

    df["close"] = df["close"].astype(float)

    return df

# =====================================
# SIGNAL LOGIC
# =====================================

def generate_signal(df):

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

    if (
        ema9.iloc[-1] > ema21.iloc[-1]
        and rsi.iloc[-1] > 55
    ):
        return "CALL"

    elif (
        ema9.iloc[-1] < ema21.iloc[-1]
        and rsi.iloc[-1] < 45
    ):
        return "PUT"

    return None

# =====================================
# CHECK RESULT
# =====================================

def check_result(before, after, signal):

    if signal == "CALL":

        if after > before:
            return "WIN"

        return "LOSS"

    elif signal == "PUT":

        if after < before:
            return "WIN"

        return "LOSS"

# =====================================
# SEND SIGNAL
# =====================================

def send_signal(pair, signal):

    global total_signal
    global total_win
    global total_loss

    total_signal += 1

    now = datetime.now()

    entry_time = now.strftime("%H:%M")

    exit_time = (
        now.timestamp() + 60
    )

    exit_time = datetime.fromtimestamp(
        exit_time
    ).strftime("%H:%M")

    pair_name = pair.replace("/", "") + "-OTC"

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

    before_df = get_data(pair)

    if before_df is None:
        return

    before_price = before_df["close"].iloc[-1]

    time.sleep(60)

    after_df = get_data(pair)

    if after_df is None:
        return

    after_price = after_df["close"].iloc[-1]

    result = check_result(
        before_price,
        after_price,
        signal
    )

    if result == "WIN":
        total_win += 1
    else:
        total_loss += 1

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

# =====================================
# MAIN BOT LOOP
# =====================================

def run_bot():

    while True:

        try:

            for pair in pairs:

                df = get_data(pair)

                if df is None:
                    continue

                signal = generate_signal(df)

                if signal:

                    send_signal(pair, signal)

                    time.sleep(10)

            time.sleep(30)

        except Exception as e:

            print("ERROR:", e)

            time.sleep(15)

# =====================================
# START
# =====================================

threading.Thread(
    target=run_bot
).start()

while True:
    time.sleep(100)