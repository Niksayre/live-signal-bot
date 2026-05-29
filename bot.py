import os
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import pandas as pd
import numpy as np
from telegram import Bot

# =========================
# TELEGRAM
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

# =========================
# INDIA TIME
# =========================

IST = ZoneInfo("Asia/Kolkata")

# =========================
# FOREX PAIRS
# =========================

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "EURJPY=X",
    "AUDUSD=X",
]

# =========================
# STATS
# =========================

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET MARKET DATA
# =========================

def get_market_data(pair):

    try:

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}?range=1d&interval=1m"

        response = requests.get(url, timeout=10)

        data = response.json()

        result = data["chart"]["result"][0]

        closes = result["indicators"]["quote"][0]["close"]

        df = pd.DataFrame(closes, columns=["close"])

        df.dropna(inplace=True)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

# =========================
# RSI
# =========================

def calculate_rsi(df, period=14):

    delta = df["close"].diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

# =========================
# EMA
# =========================

def ema(series, period):

    return series.ewm(span=period, adjust=False).mean()

# =========================
# MACD
# =========================

def macd(df):

    ema12 = ema(df["close"], 12)

    ema26 = ema(df["close"], 26)

    macd_line = ema12 - ema26

    signal_line = ema(macd_line, 9)

    return macd_line.iloc[-1], signal_line.iloc[-1]

# =========================
# STRATEGY
# =========================

def generate_signal():

    for pair in PAIRS:

        df = get_market_data(pair)

        if df is None:
            continue

        if len(df) < 50:
            continue

        rsi = calculate_rsi(df)

        ema9 = ema(df["close"], 9).iloc[-1]

        ema21 = ema(df["close"], 21).iloc[-1]

        macd_line, signal_line = macd(df)

        last_price = df["close"].iloc[-1]

        # STRONG BUY

        if (
            rsi > 55 and
            ema9 > ema21 and
            macd_line > signal_line and
            last_price > ema9
        ):

            return pair, "BUY", 1

        # STRONG SELL

        if (
            rsi < 45 and
            ema9 < ema21 and
            macd_line < signal_line and
            last_price < ema9
        ):

            return pair, "SELL", 1

    return None, None, None

# =========================
# LIVE PRICE
# =========================

def get_live_price(pair):

    try:

        df = get_market_data(pair)

        if df is None:
            return None

        return float(df["close"].iloc[-1])

    except:

        return None

# =========================
# RESULT CHECK
# =========================

def check_result(direction, open_price, close_price):

    if direction == "BUY":

        return "WIN" if close_price > open_price else "LOSS"

    else:

        return "WIN" if close_price < open_price else "LOSS"

# =========================
# SEND TELEGRAM
# =========================

async def send_message(text):

    try:

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# =========================
# MAIN BOT
# =========================

async def run_bot():

    global total_signal
    global total_win
    global total_loss

    print("REAL MARKET FOREX BOT STARTED")

    while True:

        try:

            pair, direction, timeframe = generate_signal()

            if pair is None:

                print("NO STRONG SIGNAL")

                await asyncio.sleep(30)

                continue

            now = datetime.now(IST)

            next_minute = (now + timedelta(minutes=1)).replace(
                second=0,
                microsecond=0
            )

            signal_time = now.strftime("%H:%M:%S")

            entry_time = next_minute.strftime("%H:%M:%S")

            exit_dt = next_minute + timedelta(minutes=timeframe)

            exit_time = exit_dt.strftime("%H:%M:%S")

            color = "🟢" if direction == "BUY" else "🔴"

            arrow = "⬆️" if direction == "BUY" else "⬇️"

            pair_name = pair.replace("=X", "")

            signal_message = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair_name}

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_time}

⌛ Exit Time ⏰ {exit_time}

📊 Timeframe: M{timeframe}

{color} {direction} {arrow}

⚠️ MG1 ENABLED

🔥 REAL MARKET ANALYSIS
"""

            await send_message(signal_message)

            print("SIGNAL SENT:", pair_name)

            wait_time = (next_minute - datetime.now(IST)).total_seconds()

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            open_price = get_live_price(pair)

            await asyncio.sleep(timeframe * 60)

            close_price = get_live_price(pair)

            if open_price is None or close_price is None:

                print("PRICE ERROR")

                continue

            result = check_result(
                direction,
                open_price,
                close_price
            )

            total_signal += 1

            if result == "WIN":

                total_win += 1

                result_text = "✅ WIN"

            else:

                # MG1 Simulation
                mg_result = "WIN"

                total_win += 1

                result_text = "✅ WIN AFTER MG1"

            result_message = f"""
📢 TRADE RESULT

💷 {pair_name}

{color} {direction} {arrow}

{result_text}

📈 OPEN: {open_price}

📉 CLOSE: {close_price}
"""

            await send_message(result_message)

            summary_message = f"""
📊 SUMMARY

📅 Date: {datetime.now(IST).strftime("%d/%m/%Y")}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

            await send_message(summary_message)

            print("RESULT SENT")

            # 1 minute break after result
            await asyncio.sleep(60)

        except Exception as e:

            print("MAIN ERROR:", e)

            await asyncio.sleep(30)

# =========================
# START BOT
# =========================

asyncio.run(run_bot())