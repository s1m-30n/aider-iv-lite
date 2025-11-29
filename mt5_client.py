import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

class MT5Client:
    def __init__(self):
        self.authorized = False

    def initialize(self) -> bool:
        """Initialize connection to MT5 terminal."""
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            return False
            
        login = os.getenv("LOGIN")
        password = os.getenv("PASSWORD")
        server = os.getenv("SERVER")
        
        if login and password and server:
            try:
                authorized = mt5.login(int(login), password=password, server=server)
                if authorized:
                    self.authorized = True
                    return True
                else:
                    print("failed to connect at account #{}, error code: {}".format(login, mt5.last_error()))
                    return False
            except Exception as e:
                print(f"Login failed: {e}")
                return False
        
        self.authorized = True
        return True

    def shutdown(self):
        """Shutdown connection to MT5 terminal."""
        mt5.shutdown()
        self.authorized = False

    def get_data(self, symbol: str, timeframe, num_candles: int) -> pd.DataFrame:
        """
        Get historical data for a symbol.
        
        Args:
            symbol (str): The symbol to retrieve data for.
            timeframe: MT5 timeframe constant (e.g., mt5.TIMEFRAME_M1).
            num_candles (int): Number of candles to retrieve.
            
        Returns:
            pd.DataFrame: DataFrame containing the historical data.
        """
        if not self.authorized:
            if not self.initialize():
                return pd.DataFrame()

        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
        if rates is None or len(rates) == 0:
            print(f"Failed to get data for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def place_order(self, symbol: str, order_type, volume: float, sl: float = 0.0, tp: float = 0.0, comment: str = "") -> dict:
        """
        Place a trade order.
        
        Args:
            symbol (str): The symbol to trade.
            order_type: MT5 order type (e.g., mt5.ORDER_TYPE_BUY).
            volume (float): Volume to trade.
            sl (float): Stop Loss price.
            tp (float): Take Profit price.
            comment (str): Order comment.
            
        Returns:
            dict: Result dictionary.
        """
        if not self.authorized:
            if not self.initialize():
                return None

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"Failed to get tick for {symbol}")
            return None

        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.comment}")
            return None
        
        return result._asdict()

    def modify_position(self, ticket: int, sl: float, tp: float) -> bool:
        """
        Modify an existing position (SL/TP).
        
        Args:
            ticket (int): The position ticket.
            sl (float): New Stop Loss.
            tp (float): New Take Profit.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.authorized:
            if not self.initialize():
                return False
                
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": sl,
            "tp": tp,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Modify failed: {result.comment}")
            return False
            
        return True

    def close_position(self, ticket: int) -> bool:
        """
        Close an existing position.
        
        Args:
            ticket (int): The position ticket.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.authorized:
            if not self.initialize():
                return False
        
        positions = mt5.positions_get(ticket=ticket)
        if positions is None or len(positions) == 0:
            print(f"Position {ticket} not found")
            return False
            
        position = positions[0]
        symbol = position.symbol
        volume = position.volume
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        
        tick = mt5.symbol_info_tick(symbol)
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Close failed: {result.comment}")
            return False
            
        return True

    def get_open_positions(self, symbol: str = None):
        """
        Get open positions.
        
        Args:
            symbol (str): Optional symbol to filter by.
            
        Returns:
            tuple: Tuple of positions.
        """
        if not self.authorized:
            if not self.initialize():
                return ()
                
        if symbol:
            return mt5.positions_get(symbol=symbol)
        else:
            return mt5.positions_get()

    def get_symbol_tick(self, symbol: str):
        """
        Get current tick for a symbol.
        
        Args:
            symbol (str): The symbol.
            
        Returns:
            Tick object or None.
        """
        if not self.authorized:
            if not self.initialize():
                return None
                
        return mt5.symbol_info_tick(symbol)
