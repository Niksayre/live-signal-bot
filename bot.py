import asyncio
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz

from telegram import Bot

# ============================================
# TELEGRAM CONFIG
# ============================================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# ============================================
# TIMEZONE
# ============================================

IST = pytz.timezone("Asia/Kolkata")

# ============================================
# API CONFIG
# ============================================

API_KEY = "YOUR_TWELVEDATA_API_KEY"

# ============================================
# FOREX PAIRS
# ============================================

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY",
    "GBP/JPY"
]

# ============================================
# STATISTICS
# ============================================

total_signal = 0
total_win = 0
total_loss = 0

last_trade_time = None

# ============================================
# GET REAL MARKET DATA
# ============================================

def get_market_data(symbol):

    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}"
        f"&interval=1min"
        f"&outputsize=100"
        f"&apikey={API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "values" not in data:
            return None

        df = pd.DataFrame(data["values"])

        df = df.iloc[::-1]

        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)

        return df

    except Exception as e:
        print("MARKET ERROR:", e)
        return None

# ============================================
# RSI
# ============================================

def calculate_rsi(df, period=14):

    delta = df["close"].diff()

    gain = delta.clip(lower=0)

    loss = -1 * delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

# ============================================
# EMA TREND
# ============================================

def ema_signal(df):

    ema_fast = df["close"].ewm(span=9).mean()

    ema_slow = df["close"].ewm(span=21).mean()

    if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
        return "BUY"

    elif ema_fast.iloc[-1] < ema_slow.iloc[-1]:
        return "SELL"

    return "WAIT"

# ============================================
# SUPPORT / RESISTANCE
# ============================================

def support(df):
    return df["low"].tail(20).min()

def resistance(df):
    return df["high"].tail(20).max()

# ============================================
# GENERATE SIGNAL
# ============================================

def generate_signal(symbol):

    df = get_market_data(symbol)

    if df is None or len(df) < 50:
        return None

    current_price = df["close"].iloc[-1]

    sup = support(df)

    res = resistance(df)

    rsi = calculate_rsi(df)

    trend = ema_signal(df)

    prev_close = df["close"].iloc[-2]

    bullish = current_price > prev_close

    bearish = current_price < prev_close

    near_support = abs(current_price - sup) <= 0.0015

    near_resistance = abs(current_price - res) <= 0.0015

    # BUY SIGNAL

    if (
        near_support
        and trend == "BUY"
        and rsi < 45
        and bullish
    ):

        return {
            "signal": "BUY",
            "price": current_price
        }

    # SELL SIGNAL

    if (
        near_resistance
        and trend == "SELL"
        and rsi > 55
        and bearish
    ):

        return {
            "signal": "SELL",
            "price": current_price
        }

    return None

# ============================================
# FORMAT SIGNAL
# ============================================

def create_signal_message(pair, signal, signal_time, entry, exit_time):

    if signal == "BUY":

        side = "🟢 BUY ⬆️"

    else:

        side = "🔴 SELL ⬇️"

    msg = f"""
🚧 LIVE FOREX SIGNAL

💷 {pair}

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry}

⌛ Exit Time ⏰ {exit_time}

📊 Timeframe: M1

{side}

⚠️ MG1 ENABLED

🔥 REAL MARKET SIGNAL
"""

    return msg

# ============================================
# CHECK RESULT
# ============================================

def check_result(signal_type, entry_price, close_price):

    if signal_type == "BUY":

        return close_price > entry_price

    else:

        return close_price < entry_price

# ============================================
# SEND RESULT
# ============================================

async def send_result(pair, signal_type, result, mg=False):

    global total_win
    global total_loss

    if signal_type == "BUY":
        side = "🟢 BUY ⬆️"
    else:
        side = "🔴 SELL ⬇️"

    if result:

        if mg:
            res = "✅ WIN MG1"
        else:
            res = "✅ WIN"

        total_win += 1

    else:

        res = "❌ LOSS"

        total_loss += 1

    msg = f"""
📢 TRADE RESULT

💷 {pair}

{side}

{res}
"""

    await bot.send_message(chat_id=CHAT_ID, text=msg)

# ============================================
# SEND SUMMARY
# ============================================

async def send_summary():

    msg = f"""
📊 SUMMARY

📅 Date: {datetime.now(IST).strftime('%d/%m/%Y')}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

    await bot.send_message(chat_id=CHAT_ID, text=msg)

# ============================================
# MAIN BOT LOOP
# ============================================

async def run_bot():

    global total_signal
    global last_trade_time

    print("LIVE FOREX BOT STARTED")

    while True:

        try:

            now = datetime.now(IST)

            # NO CONTINUOUS SPAM

            if last_trade_time:

                diff = (now - last_trade_time).seconds

                if diff < 60:

                    await asyncio.sleep(5)
                    continue

            found_signal = False

            for pair in PAIRS:

                print(f"CHECKING {pair}")

                signal_data = generate_signal(pair)

                if signal_data is None:
                    continue

                found_signal = True

                total_signal += 1

                signal_type = signal_data["signal"]

                signal_time = now.strftime("%H:%M:%S")

                # ENTRY NEXT MINUTE

                entry_time_dt = (now + timedelta(minutes=1)).replace(second=0)

                exit_time_dt = entry_time_dt + timedelta(minutes=1)

                entry_time = entry_time_dt.strftime("%H:%M:%S")

                exit_time = exit_time_dt.strftime("%H:%M:%S")

                message = create_signal_message(
                    pair,
                    signal_type,
                    signal_time,
                    entry_time,
                    exit_time
                )

                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=message
                )

                last_trade_time = datetime.now(IST)

                # WAIT FOR ENTRY

                wait_entry = (entry_time_dt - datetime.now(IST)).total_seconds()

                if wait_entry > 0:
                    await asyncio.sleep(wait_entry)

                # ENTRY PRICE

                entry_df = get_market_data(pair)

                if entry_df is None:
                    continue

                entry_price = entry_df["close"].iloc[-1]

                # WAIT FOR EXIT

                wait_exit = (exit_time_dt - datetime.now(IST)).total_seconds()

                if wait_exit > 0:
                    await asyncio.sleep(wait_exit)

                # CLOSE PRICE

                close_df = get_market_data(pair)

                if close_df is None:
                    continue

                close_price = close_df["close"].iloc[-1]

                # DIRECT RESULT

                win = check_result(
                    signal_type,
                    entry_price,
                    close_price
                )

                # ====================================
                # DIRECT WIN
                # ====================================

                if win:

                    await send_result(
                        pair,
                        signal_type,
                        True,
                        False
                    )

                # ====================================
                # MG1
                # ====================================

                else:

                    mg_entry_dt = datetime.now(IST).replace(second=0) + timedelta(minutes=1)

                    mg_exit_dt = mg_entry_dt + timedelta(minutes=1)

                    wait_mg = (mg_entry_dt - datetime.now(IST)).total_seconds()

                    if wait_mg > 0:
                        await asyncio.sleep(wait_mg)

                    mg_entry_df = get_market_data(pair)

                    if mg_entry_df is None:
                        continue

                    mg_entry_price = mg_entry_df["close"].iloc[-1]

                    wait_mg_exit = (mg_exit_dt - datetime.now(IST)).total_seconds()

                    if wait_mg_exit > 0:
                        await asyncio.sleep(wait_mg_exit)

                    mg_close_df = get_market_data(pair)

                    if mg_close_df is None:
                        continue

                    mg_close_price = mg_close_df["close"].iloc[-1]

                    mg_win = check_result(
                        signal_type,
                        mg_entry_price,
                        mg_close_price
                    )

                    await send_result(
                        pair,
                        signal_type,
                        mg_win,
                        True
                    )

                # SUMMARY AFTER RESULT

                await send_summary()

                # 1 MIN BREAK AFTER TRADE

                await asyncio.sleep(60)

                break

            if not found_signal:
                print("NO STRONG SIGNAL")

            await asyncio.sleep(15)

        except Exception as e:

            print("BOT ERROR:", e)

            await asyncio.sleep(10)

# ============================================
# START BOT
# ============================================

asyncio.run(run_bot())
