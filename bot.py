import requests
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# =========================
# TELEGRAM + API
# =========================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"
API_KEY = "edf95432c6e84ca98d8f2a8c900e7e05"

bot = Bot(token=BOT_TOKEN)

# =========================
# INDIAN TIME
# =========================

IST = pytz.timezone("Asia/Kolkata")

# =========================
# PAIRS
# =========================

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# =========================
# SUMMARY
# =========================

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# FETCH REAL MARKET DATA
# =========================

def get_candles(pair):

    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=10&apikey={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "values" not in data:
            print("API ERROR:", data)
            return None

        return data["values"]

    except Exception as e:
        print("PRICE ERROR:", e)
        return None

# =========================
# SIGNAL LOGIC
# =========================

def generate_signal(candles):

    try:
        close1 = float(candles[0]["close"])
        open1 = float(candles[0]["open"])

        close2 = float(candles[1]["close"])
        open2 = float(candles[1]["open"])

        high1 = float(candles[0]["high"])
        low1 = float(candles[0]["low"])

        body = abs(close1 - open1)
        range_candle = abs(high1 - low1)

        # Strong candle filter
        if range_candle == 0:
            return None

        strength = body / range_candle

        # Need strong candle
        if strength < 0.65:
            return None

        # BUY
        if close1 > open1 and close2 > open2:
            return "BUY"

        # SELL
        if close1 < open1 and close2 < open2:
            return "SELL"

        return None

    except:
        return None

# =========================
# CHECK RESULT
# =========================

def check_result(signal, entry, close):

    if signal == "BUY":

        if close > entry:
            return "WIN"

        else:
            return "LOSS"

    else:

        if close < entry:
            return "WIN"

        else:
            return "LOSS"

# =========================
# SEND TELEGRAM MESSAGE
# =========================

async def await send_message(text):

    try:
        await bot.await send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="HTML"
        )

    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# TRADE SYSTEM
# =========================

async def process_trade(pair):

    global total_signal
    global total_win
    global total_loss

    candles = get_candles(pair)

    if candles is None:
        return

    signal = generate_signal(candles)

    if signal is None:
        print("No strong setup found")
        return

    india_time = datetime.now(IST)

    signal_time = india_time.strftime("%H:%M:%S")

    entry_time_dt = india_time + timedelta(minutes=1)
    exit_time_dt = entry_time_dt + timedelta(minutes=1)

    entry_time = entry_time_dt.strftime("%H:%M:%S")
    exit_time = exit_time_dt.strftime("%H:%M:%S")

    total_signal += 1

    direction = ""
    color = ""

    if signal == "BUY":
        direction = "🟢 BUY ⬆️ UP"
        color = "🟢"

    else:
        direction = "🔴 SELL ⬇️ DOWN"
        color = "🔴"

    # =========================
    # SEND SIGNAL
    # =========================

    signal_message = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💱 <b>{pair}</b>

🕒 Signal Time: {signal_time}

⏳ Entry Time: {entry_time}

⌛ Exit Time: {exit_time}

📊 Timeframe: M1

{direction}

⚠️ MG1 ENABLED

🔥 REAL MARKET DATA
"""

    await await send_message(signal_message)

    # =========================
    # WAIT FOR ENTRY
    # =========================

    await asyncio.sleep(60)

    entry_candles = get_candles(pair)

    if entry_candles is None:
        return

    entry_price = float(entry_candles[0]["close"])

    # =========================
    # WAIT FOR EXIT
    # =========================

    await asyncio.sleep(60)

    exit_candles = get_candles(pair)

    if exit_candles is None:
        return

    exit_price = float(exit_candles[0]["close"])

    result = check_result(signal, entry_price, exit_price)

    mg_used = False

    # =========================
    # MG1
    # =========================

    if result == "LOSS":

        mg_used = True

        await asyncio.sleep(60)

        mg_candles = get_candles(pair)

        if mg_candles is None:
            return

        mg_close = float(mg_candles[0]["close"])

        result = check_result(signal, exit_price, mg_close)

    # =========================
    # FINAL RESULT
    # =========================

    if result == "WIN":

        total_win += 1

        if mg_used:
            result_text = "✅ WIN AFTER MG1"
        else:
            result_text = "✅ DIRECT WIN"

    else:

        total_loss += 1
        result_text = "❌ LOSS"

    # =========================
    # SEND RESULT
    # =========================

    result_message = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair}</b>

{direction}

{result_text}
"""

    await await send_message(result_message)

    # =========================
    # WINRATE
    # =========================

    if total_signal > 0:
        winrate = round((total_win / total_signal) * 100, 2)
    else:
        winrate = 0

    # =========================
    # SUMMARY
    # =========================

    summary = f"""
📊 <b>SUMMARY</b>

📅 Date: {india_time.strftime("%d/%m/%Y")}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}

📈 Winrate: {winrate}%
"""

    await await send_message(summary)

    # =========================
    # 1 MIN BREAK
    # =========================

    await asyncio.sleep(60)

# =========================
# MAIN LOOP
# =========================

async def main():

    print("LIVE FOREX BOT STARTED")

    while True:

        for pair in pairs:

            try:
                await process_trade(pair)

                # API LIMIT PROTECTION
                await asyncio.sleep(10)

            except Exception as e:
                print("MAIN ERROR:", e)

        await asyncio.sleep(20)

# =========================
# START
# =========================

asyncio.run(main())
