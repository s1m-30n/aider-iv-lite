import MetaTrader5 as mt5
for x in dir(mt5):
    if 'FILLING' in x:
        print(x)
