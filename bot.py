import asyncio
import requests
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# ==========================================
# TELEGRAM SETTINGS
# ==========================================

BOT_TOKEN = "8926681279:AAEa-0EQpSoCMTbldp0GE03LNAs5wBNwKqY"
CHAT_ID = "8241640506"

bot = Bot(token=BOT_TOKEN)

# ==========================================
# INDIA TIME
# ==========================================

IST = pytz.timezone("Asia/Kolkata")

# ==========================================
# FOREX PAIRS
# ==========================================

pairs = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "EURJPY",
    "AUDUSD",
    "USDCAD",
    "GBPJPY",
    "EURGBP"
]

# ==========================================
# GLOBAL STATS
# ==========================================

total_signal = 0
total_win = 0
total_loss = 0

last_trade_time = None

# ==========================================
# GET LIVE MARKET DATA
# ==========================================

def get_prices(pair):

    try:

        symbol = pair + "=X"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"

        response = requests.get(url, timeout=10)

        data = response.json()

        prices = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

        clean_prices = []

        for p in prices:
            if p is not None:
                clean_prices.append(p)

        return clean_prices[-10:]

    except Exception as e:

        print("PRICE ERROR:", e)

        return None

# ==========================================
# SUPPORT / RESISTANCE
# ==========================================

def support_resistance(prices):

    support = min(prices[-5:])

    resistance = max(prices[-5:])

    return support, resistance

# ==========================================
# WINRATE
# ==========================================

def calculate_winrate():

    global total_signal
    global total_win

    if total_signal == 0:
        return 0

    return round((total_win / total_signal) * 100, 2)

# ==========================================
# REAL SIGNAL LOGIC
# ==========================================

def generate_signal():

    global last_trade_time

    now = datetime.now(IST)

    # ======================================
    # NO CONTINUOUS SPAM
    # ======================================

    if last_trade_time:

        diff = (now - last_trade_time).seconds

        if diff < 180:
            return None

    best_signal = None

    best_strength = 0

    # ======================================
    # CHECK ALL PAIRS
    # ======================================

    for pair in pairs:

        prices = get_prices(pair)

        if not prices:
            continue

        if len(prices) < 6:
            continue

        current = prices[-1]

        previous = prices[-2]

        support, resistance = support_resistance(prices)

        # ==================================
        # MOMENTUM
        # ==================================

        bullish = 0
        bearish = 0

        for i in range(-5, -1):

            if prices[i + 1] > prices[i]:
                bullish += 1

            elif prices[i + 1] < prices[i]:
                bearish += 1

        movement = abs(current - previous)

        # ==================================
        # STRONG BUY
        # ==================================

        if bullish >= 3 and current > support:

            if movement > best_strength:

                best_strength = movement

                best_signal = {
                    "pair": pair,
                    "direction": "BUY"
                }

        # ==================================
        # STRONG SELL
        # ==================================

        if bearish >= 3 and current < resistance:

            if movement > best_strength:

                best_strength = movement

                best_signal = {
                    "pair": pair,
                    "direction": "SELL"
                }

    # ======================================
    # NO SETUP
    # ======================================

    if not best_signal:
        return None

    # ======================================
    # TIMES
    # ======================================

    signal_time = now

    entry_time = (
        now + timedelta(minutes=1)
    ).replace(second=0, microsecond=0)

    expiry_time = entry_time + timedelta(minutes=1)

    last_trade_time = now

    return {
        "pair": best_signal["pair"],
        "direction": best_signal["direction"],
        "signal_time": signal_time,
        "entry_time": entry_time,
        "expiry_time": expiry_time
    }

# ==========================================
# RESULT CHECK
# ==========================================

def check_result(pair, direction):

    prices = get_prices(pair)

    if not prices:
        return "LOSS"

    open_price = prices[-2]

    close_price = prices[-1]

    # ======================================
    # BUY
    # ======================================

    if direction == "BUY":

        if close_price > open_price:
            return "WIN"
        else:
            return "LOSS"

    # ======================================
    # SELL
    # ======================================

    else:

        if close_price < open_price:
            return "WIN"
        else:
            return "LOSS"

# ==========================================
# SEND SIGNAL
# ==========================================

async def send_signal(signal):

    pair = signal["pair"]

    direction = signal["direction"]

    signal_time = signal["signal_time"].strftime("%H:%M:%S")

    entry_time = signal["entry_time"].strftime("%H:%M:%S")

    exit_time = signal["expiry_time"].strftime("%H:%M:%S")

    if direction == "BUY":

        color = "🟢"

        arrow = "⬆️"

        side = "UP"

    else:

        color = "🔴"

        arrow = "⬇️"

        side = "DOWN"

    message = f"""
🚨 <b>LIVE FOREX SIGNAL</b>

💱 <b>{pair}-FX</b>

🕒 Signal Time ⏰ {signal_time}

⏳ Entry Time ⏰ {entry_time}

⌛ Exit Time ⏰ {exit_time}

📊 Timeframe: M1

{color} <b>{direction}</b> {arrow}

📈 Direction: <b>{side}</b>

⚠️ MG1 ENABLED

🔥 REAL MARKET ANALYSIS
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode="HTML"
    )

# ==========================================
# SEND RESULT + SUMMARY
# ==========================================

async def send_result(signal, result):

    global total_signal
    global total_win
    global total_loss

    pair = signal["pair"]

    direction = signal["direction"]

    total_signal += 1

    # ======================================
    # BUY STYLE
    # ======================================

    if direction == "BUY":

        color = "🟢"

        arrow = "⬆️"

    else:

        color = "🔴"

        arrow = "⬇️"

    # ======================================
    # RESULT
    # ======================================

    if "WIN" in result:

        total_win += 1

        result_text = f"✅ {result}"

    else:

        total_loss += 1

        result_text = "❌ LOSS"

    # ======================================
    # WINRATE
    # ======================================

    winrate = calculate_winrate()

    # ======================================
    # RESULT MESSAGE
    # ======================================

    result_message = f"""
📢 <b>TRADE RESULT</b>

💱 <b>{pair}-FX</b>

{color} <b>{direction}</b> {arrow}

{result_text}
"""

    # ======================================
    # SUMMARY
    # ======================================

    summary = f"""
📊 <b>SUMMARY</b>

📅 Date: {datetime.now(IST).strftime('%d/%m/%Y')}

🎯 Total Signal: {total_signal}

✅ Total Win: {total_win}

❌ Total Loss: {total_loss}

🏆 Winrate: {winrate}%
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=result_message,
        parse_mode="HTML"
    )

    await bot.send_message(
        chat_id=CHAT_ID,
        text=summary,
        parse_mode="HTML"
    )

# ==========================================
# MAIN BOT LOOP
# ==========================================

async def main():

    print("LIVE FOREX BOT STARTED")

    while True:

        try:

            now = datetime.now(IST)

            # ==================================
            # ONLY CHECK NEW MINUTE
            # ==================================

            if now.second < 5:

                signal = generate_signal()

                # ==============================
                # SIGNAL FOUND
                # ==============================

                if signal:

                    await send_signal(signal)

                    current = datetime.now(IST)

                    wait_time = (
                        signal["expiry_time"] - current
                    ).total_seconds()

                    # ==========================
                    # WAIT CANDLE CLOSE
                    # ==========================

                    if wait_time > 0:

                        await asyncio.sleep(wait_time)

                    # ==========================
                    # CHECK RESULT
                    # ==========================

                    result = check_result(
                        signal["pair"],
                        signal["direction"]
                    )

                    # ==========================
                    # MG1
                    # ==========================

                    if result == "LOSS":

                        await asyncio.sleep(60)

                        mg1_result = check_result(
                            signal["pair"],
                            signal["direction"]
                        )

                        if mg1_result == "WIN":

                            result = "WIN (MG1)"

                    # ==========================
                    # SEND RESULT
                    # ==========================

                    await send_result(signal, result)

                    # ==========================
                    # 1 MIN BREAK
                    # ==========================

                    await asyncio.sleep(60)

                else:

                    await asyncio.sleep(10)

            else:

                await asyncio.sleep(1)

        except Exception as e:

            print("BOT ERROR:", e)

            await asyncio.sleep(30)

# ==========================================
# START BOT
# ==========================================

asyncio.run(main())
