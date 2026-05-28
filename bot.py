def generate_signal(df):

    try:

        last = df.iloc[-1]
        prev = df.iloc[-2]

        current_close = last["close"]
        current_open = last["open"]

        previous_close = prev["close"]

        candle_size = abs(current_close - current_open)

        # BUY SIGNAL

        if (

            current_close > current_open

            and current_close > previous_close

            and candle_size > 0.00005

        ):

            return "BUY"

        # SELL SIGNAL

        elif (

            current_close < current_open

            and current_close < previous_close

            and candle_size > 0.00005

        ):

            return "SELL"

        # FORCE SIGNAL IF MARKET MOVING

        elif current_close > previous_close:

            return "BUY"

        else:

            return "SELL"

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None