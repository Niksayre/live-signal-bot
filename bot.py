```python
import requests
import time
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# =========================
# TELEGRAM CONFIG
# =========================

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

bot = Bot(token=BOT_TOKEN)

# =========================
# SETTINGS
# =========================

TIMEZONE = pytz.timezone("Asia/Kolkata")

PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "EURJPY",
    "AUDUSD",
    "USDCAD"
]

TIMEFRAMES = {
    "M1": 1,
    "M2": 2,
    "M5": 5
}

MG_ENABLED = True

total_signal = 0
total_win = 0
total_loss = 0

# =========================
# GET LIVE FOREX DATA
# =========================

def get_forex_data(pair):

    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=120&apikey=demo"

    try:
        response = requests.get(url).json()

        candles = response["values"]

        closes = [float(x["close"]) for x in candles]
        highs = [float(x["high"]) for x in candles]
        lows = [float(x["low"]) for x in candles]
        opens = [float(x["open"]) for x in candles]

        return opens, highs, lows, closes

    except:
        return None

# =========================
# EMA
# =========================

def ema(data, period):

    multiplier = 2 / (period + 1)

    ema_values = [sum(data[:period]) / period]

    for price in data[period:]:
        ema_values.append(
            (price - ema_values[-1]) * multiplier + ema_values[-1]
        )

    return ema_values[-1]

# =========================
# RSI
# =========================

def rsi(closes, period=14):

    gains = []
    losses = []

    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]

        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

# =========================
# MACD
# =========================

def macd(closes):

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)

    return ema12 - ema26

# =========================
# STRONG TREND FILTER
# =========================

def strong_trend(closes):

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)

    distance = abs(ema20 - ema50)

    return distance > 0.0005

# =========================
# SIGNAL LOGIC
# =========================

def generate_signal(pair):

    data = get_forex_data(pair)

    if not data:
        return None

    opens, highs, lows, closes = data

    current = closes[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)

    current_rsi = rsi(closes)

    current_macd = macd(closes)

    bullish_candle = closes[-1] > opens[-1]
    bearish_candle = closes[-1] < opens[-1]

    trend_ok = strong_trend(closes)

    # =========================
    # BUY SIGNAL
    # =========================

    if (
        ema20 > ema50 and
        current_rsi > 55 and
        current_macd > 0 and
        bullish_candle and
        trend_ok
    ):

        return "BUY"

    # =========================
    # SELL SIGNAL
    # =========================

    if (
        ema20 < ema50 and
        current_rsi < 45 and
        current_macd < 0 and
        bearish_candle and
        trend_ok
    ):

        return "SELL"

    return None

# =========================
# SEND TELEGRAM
# =========================

async def send_message(text):

    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="HTML"
        )

    except Exception as e:
        print(e)

# =========================
# RESULT CHECK
# =========================

def check_result(direction, entry, exit):

    if direction == "BUY":

        if exit > entry:
            return "WIN"
        else:
            return "LOSS"

    if direction == "SELL":

        if exit < entry:
            return "WIN"
        else:
            return "LOSS"

# =========================
# MAIN LOOP
# =========================

async def run_bot():

    global total_signal
    global total_win
    global total_loss

    print("LIVE FOREX SIGNAL BOT STARTED")

    while True:

        now = datetime.now(TIMEZONE)

        current_second = now.second

        # EXACTLY 1 MIN BEFORE
        if current_second == 0:

            print("CHECKING LIVE FOREX")

            for pair in PAIRS:

                signal = generate_signal(pair)

                if signal:

                    tf_name = "M5"
                    tf_minutes = 5

                    entry_time = (
                        now + timedelta(minutes=1)
                    ).replace(second=0)

                    exit_time = entry_time + timedelta(minutes=tf_minutes)

                    signal_time = now.strftime("%H:%M:%S")

                    entry_str = entry_time.strftime("%H:%M:%S")
                    exit_str = exit_time.strftime("%H:%M:%S")

                    total_signal += 1

                    if signal == "BUY":

                        signal_text = f"""
🚧 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}-FX</b>

Signal Time ⏰ <b>{signal_time}</b>

Entry ⏳ <b>{entry_str}</b>

Exit ⏳ <b>{exit_str}</b>

⌚️ <b>{tf_name}</b>

🟢 <b>BUY / UP</b>

⚠️ <b>MG1 ENABLED</b>
"""

                    else:

                        signal_text = f"""
🚧 <b>LIVE FOREX SIGNAL</b>

💷 <b>{pair}-FX</b>

Signal Time ⏰ <b>{signal_time}</b>

Entry ⏳ <b>{entry_str}</b>

Exit ⏳ <b>{exit_str}</b>

⌚️ <b>{tf_name}</b>

🔴 <b>SELL / DOWN</b>

⚠️ <b>MG1 ENABLED</b>
"""

                    await send_message(signal_text)

                    print(f"SIGNAL SENT: {pair}")

                    # WAIT FOR ENTRY
                    wait_seconds = (
                        entry_time - datetime.now(TIMEZONE)
                    ).total_seconds()

                    if wait_seconds > 0:
                        await asyncio.sleep(wait_seconds)

                    # ENTRY PRICE
                    entry_data = get_forex_data(pair)

                    entry_price = entry_data[3][-1]

                    # WAIT EXIT
                    wait_exit = (
                        exit_time - datetime.now(TIMEZONE)
                    ).total_seconds()

                    if wait_exit > 0:
                        await asyncio.sleep(wait_exit)

                    exit_data = get_forex_data(pair)

                    exit_price = exit_data[3][-1]

                    result = check_result(
                        signal,
                        entry_price,
                        exit_price
                    )

                    # =========================
                    # MARTINGALE
                    # =========================

                    mg_text = ""

                    if result == "LOSS" and MG_ENABLED:

                        mg_text = "\n⚠️ MG1 LOSS"

                        total_loss += 1

                    else:

                        total_win += 1

                        mg_text = "\n🔥 DIRECT WIN"

                    # =========================
                    # RESULT
                    # =========================

                    result_text = f"""
✅ <b>RESULT</b>

💷 <b>{pair}-FX</b>

{'🟢 BUY / UP' if signal == 'BUY' else '🔴 SELL / DOWN'}

🏆 <b>{result}</b>

{mg_text}
"""

                    await send_message(result_text)

                    # =========================
                    # SUMMARY
                    # =========================

                    summary = f"""
📊 <b>SUMMARY</b>

📅 Date: {now.strftime('%d/%m/%Y')}

📈 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}
"""

                    await send_message(summary)

                    # =========================
                    # 1 MIN BREAK
                    # =========================

                    await asyncio.sleep(60)

        await asyncio.sleep(1)

# =========================
# START
# =========================

asyncio.run(run_bot())
```
