import os
import time
import requests
import pandas as pd

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

print("LIVE FOREX MARTINGALE BOT STARTED")

# =========================================
# INDIA TIMEZONE
# =========================================

IST = ZoneInfo("Asia/Kolkata")

# =========================================
# ENV VARIABLES
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_KEY = os.getenv("API_KEY")

# =========================================
# CHECK VARIABLES
# =========================================

if not BOT_TOKEN:
    print("BOT_TOKEN NOT FOUND")

if not CHANNEL_ID:
    print("CHANNEL_ID NOT FOUND")

if not API_KEY:
    print("API_KEY NOT FOUND")

# =========================================
# FOREX PAIRS
# =========================================

pairs = [
    "EUR/USD",
    "GBP/USD"
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

def send_message(text):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": CHANNEL_ID,
            "text": text
        }

        response = requests.post(
            url,
            data=data,
            timeout=20
        )

        print("TELEGRAM STATUS:", response.status_code)

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================================
# GET LIVE FOREX DATA
# =========================================

def get_data(symbol, timeframe):

    try:

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol={symbol}"
            f"&interval={timeframe}"
            f"&outputsize=200"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url, timeout=20)

        data = response.json()

        if "values" not in data:

            print("NO DATA:", symbol)

            return None

        df = pd.DataFrame(data["values"])

        df = df.iloc[::-1]

        for col in ["open", "high", "low", "close"]:

            df[col] = df[col].astype(float)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

# =========================================
# GENERATE SIGNAL
# =========================================

def generate_signal(df, higher_df):

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

        adx = ADXIndicator(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=14
        ).adx()

        bb = BollingerBands(
            close=df["close"],
            window=20
        )

        higher_ema = EMAIndicator(
            close=higher_df["close"],
            window=50
        ).ema_indicator()

        close_price = df["close"].iloc[-1]
        open_price = df["open"].iloc[-1]

        bullish = close_price > open_price
        bearish = close_price < open_price

        # BUY SIGNAL

        if (

            ema9.iloc[-1] > ema21.iloc[-1]

            and rsi.iloc[-1] > 52

            and macd.iloc[-1] > 0

            and adx.iloc[-1] > 18

            and close_price > higher_ema.iloc[-1]

            and bullish

            and close_price < bb.bollinger_hband().iloc[-1]

        ):

            return "BUY"

        # SELL SIGNAL

        elif (

            ema9.iloc[-1] < ema21.iloc[-1]

            and rsi.iloc[-1] < 48

            and macd.iloc[-1] < 0

            and adx.iloc[-1] > 18

            and close_price < higher_ema.iloc[-1]

            and bearish

            and close_price > bb.bollinger_lband().iloc[-1]

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

        timeframe = "1min"

        duration = 60

        print("CHECKING:", pair)

        # GET DATA

        df = get_data(pair, timeframe)

        higher_df = get_data(pair, "5min")

        if df is None or higher_df is None:

            print("DATA FAILED")

            return

        # GENERATE SIGNAL

        signal = generate_signal(df, higher_df)

        if signal is None:

            print("NO STRONG SIGNAL:", pair)

            return

        pair_name = pair.replace("/", "")

        # TIMES

        entry_dt = next_candle()

        exit_dt = entry_dt + timedelta(seconds=60)

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

        send_message(signal_message)

        print("SIGNAL SENT:", pair_name)

        # =====================================
        # WAIT ENTRY
        # =====================================

        while datetime.now(IST) < entry_dt:

            time.sleep(1)

        # ENTRY PRICE

        entry_df = get_data(pair, timeframe)

        if entry_df is None:

            return

        entry_price = entry_df["close"].iloc[-1]

        print("ENTRY PRICE:", entry_price)

        # WAIT CLOSE

        time.sleep(duration)

        # EXIT PRICE

        exit_df = get_data(pair, timeframe)

        if exit_df is None:

            return

        exit_price = exit_df["close"].iloc[-1]

        print("EXIT PRICE:", exit_price)

        # CHECK RESULT

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

            print("WIN SENT")

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

            time.sleep(60)

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

            # MG1 RESULT

            if mg_result == "WIN":

                total_win += 1

                mg_message = f"""
✅ MG1 RESULT

💷 {pair_name}

{signal}

WIN
"""

                send_message(mg_message)

                print("MG1 WIN")

            else:

                total_loss += 1

                mg_message = f"""
❌ MG1 RESULT

💷 {pair_name}

{signal}

LOSS
"""

                send_message(mg_message)

                print("MG1 LOSS")

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

        time.sleep(30)

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

            # API LIMIT PROTECTION
            time.sleep(60)

        # MAIN WAIT
        time.sleep(120)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        time.sleep(60)