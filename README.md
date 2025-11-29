# Aider Lite

Aider Lite is a bot for technical analysis of Deriv Boom and Crash markets.

It checks for scalp, swing and trend trade opportunitied.
For Boom it trades for sell opportunities only and for Crash it trades for buy opportunities only.

Pairs to check include:

- Boom 500 Index
- Crash 500 Index
- Boom 600 Index
- Crash 600 Index
- Boom 900 Index
- Crash 900 Index
- Boom 1000 Index
- Crash 1000 Index

Using indicators from ta-lib and data from metatrader5.
Indicators:

- Bollinger Bands
- RSI
- MACD
- Stochastic
- ATR
- EMA
- Price Action

If it notices a trade opportunity, it will open a trade, then set tp and sl, then provide an option monitor it so as to add trailing stop.
