def generate_signal(df):

    try:

        close = df["close"]

        ema3 = EMAIndicator(
            close=close,
            window=3
        ).ema_indicator()

        ema5 = EMAIndicator(
            close=close,
            window=5
        ).ema_indicator()

        rsi = RSIIndicator(
            close=close,
            window=7
        ).rsi()

        current = close.iloc[-1]

        previous = close.iloc[-2]

        # BUY SIGNAL

        if (

            ema3.iloc[-1] > ema5.iloc[-1]

            and rsi.iloc[-1] > 48

            and current > previous

        ):

            return "BUY"

        # SELL SIGNAL

        elif (

            ema3.iloc[-1] < ema5.iloc[-1]

            and rsi.iloc[-1] < 52

            and current < previous

        ):

            return "SELL"

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None
