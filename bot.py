import os
import time
import requests
import pandas as pd

from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta

print("HIGH ACCURACY FOREX BOT STARTED")

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
    "GBP/JPY",
    "USD/JPY",
    "EUR/JPY",
    "GBP/USD"
]

# =========================================
# SUMMARY
# =========================================

total_signal = 0
total_win = 0
total_loss = 0

# =========================================
# TELEGRAM
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
# GET DATA
# =========================================

def get_data(symbol, timeframe):

    try:

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol={symbol}"
            f"&interval={timeframe}"
            f"&outputsize=250"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url)

        data = response.json()

        if "values" not in data:
            return None

        df = pd.DataFrame(data["values"])

        df = df.iloc[::-1]

        # CONVERT

        for col in ["open", "high", "low", "close"]:

            df[col] = df[col].astype(float)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

# =========================================
# HIGH ACCURACY STRATEGY
# =========================================

def generate_signal(df, higher_df):

    try:

        # ==========================
        # MAIN TIMEFRAME
        # ==========================

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

        adx = ADXIndicator(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=14
        ).adx()

        # ==========================
        # HIGHER TIMEFRAME TREND
        # ==========================

        higher_ema = EMAIndicator(
            close=higher_df["close"],
            window=50
        ).ema_indicator()

        # ==========================
        # LAST VALUES
        # ==========================

        last_close = df["close"].iloc[-1]

        last_ema9 = ema9.iloc[-1]
        last_ema21 = ema21.iloc[-1]

        last_rsi = rsi.iloc[-1]

        last_macd = macd.iloc[-1]

        last_adx = adx.iloc[-1]

        higher_trend = higher_ema.iloc[-1]

        # ==========================
        # CANDLE CONFIRMATION
        # ==========================

        last_open = df["open"].iloc[-1]

        bullish_candle = last_close > last_open

        bearish_candle = last_close < last_open

        # ===================================
        # STRONG BUY
        # ===================================

        if (

            last_ema9 > last_ema21

            and last_rsi > 58

            and last_macd > 0

            and last_adx > 25

            and last_close > higher_trend

            and bullish_candle

        ):

            return "BUY"

        # ===================================
        # STRONG SELL
        # ===================================

        elif (

            last_ema9 < last_ema21

            and last_rsi < 42

            and last_macd < 0

            and last_adx > 25

            and last_close < higher_trend

            and bearish_candle

        ):

            return "SELL"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

# =========================================
# RESULT
# =========================================

def check_result(entry, exitp, signal):

    if signal == "BUY":

        return "WIN" if exitp > entry else "LOSS"

    if signal == "SELL":

        return "WIN" if exitp < entry else "LOSS"

    return "LOSS"

# =========================================
# NEXT EXACT CANDLE
# =========================================

def next_candle():

    now = datetime.now()

    return (
        now.replace(second=0, microsecond=0)
        + timedelta(minutes=1)
    )

# =========================================
# PROCESS TRADE
# =========================================

def process_trade(pair, timeframe, duration):

    global total_signal
    global total_win
    global total_loss

    try:

        df = get_data(pair, timeframe)

        higher_df = get_data(pair, "5min")

        if df is None or higher_df is None:
            return

        signal = generate_signal(df, higher_df)

        if signal is None:

            print("NO STRONG SIGNAL:", pair)

            return

        pair_name = pair.replace("/", "")

        entry_dt = next_candle()

        exit_dt = entry_dt + timedelta(seconds=duration)

        signal_time = datetime.now().strftime("%H:%M:%S")

        entry_time = entry_dt.strftime("%H:%M:00")

        exit_time = exit_dt.strftime("%H:%M:00")

        total_signal += 1

        # ===================================
        # SIGNAL
        # ===================================

        signal_message = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair_name}

Signal Time ⏰ {signal_time}

Entry ⏳ {entry_time}

Exit ⏳ {exit_time}

⌚️ {timeframe.upper()}

{"🟢 BUY" if signal == "BUY" else "🔴 SELL"}
"""

        send_message(signal_message)

        print("SIGNAL SENT:", pair_name)

        # WAIT FOR ENTRY

        while datetime.now() < entry_dt:

            time.sleep(1)

        # ENTRY PRICE

        entry_df = get_data(pair, timeframe)

        if entry_df is None:
            return

        entry_price = entry_df["close"].iloc[-1]

        # WAIT TRADE TIME

        time.sleep(duration)

        # EXIT PRICE

        exit_df = get_data(pair, timeframe)

        if exit_df is None:
            return

        exit_price = exit_df["close"].iloc[-1]

        # RESULT

        result = check_result(
            entry_price,
            exit_price,
            signal
        )

        if result == "WIN":

            total_win += 1

        else:

            total_loss += 1

        # ===================================
        # RESULT MESSAGE
        # ===================================

        result_message = f"""
✅ RESULT

💷 {pair_name}

{signal}

{result}
"""

        send_message(result_message)

        # ===================================
        # SUMMARY
        # ===================================

        summary_message = f"""
📊 SUMMARY

Date: {datetime.now().strftime("%d/%m/%Y")}

Total Signal: {total_signal}

Total Win: {total_win}

Total Loss: {total_loss}
"""

        send_message(summary_message)

        print("RESULT + SUMMARY SENT")

        # WAIT

        time.sleep(10)

    except Exception as e:

        print("PROCESS ERROR:", e)

# =========================================
# MAIN LOOP
# =========================================

while True:

    try:

        print("CHECKING LIVE FOREX MARKET")

        # 1 MIN

        for pair in pairs:

            process_trade(
                pair=pair,
                timeframe="1min",
                duration=60
            )

        # 2 MIN

        for pair in pairs:

            process_trade(
                pair=pair,
                timeframe="2min",
                duration=120
            )

        # 5 MIN

        for pair in pairs:

            process_trade(
                pair=pair,
                timeframe="5min",
                duration=300
            )

        time.sleep(20)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        time.sleep(20)
