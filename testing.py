import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time

    # establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

def market_order():
    tick = mt5.symbol_info_tick(SYMBOL)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": VOLUME,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "deviation": DEVIATION,
        "magic": 100,
        "comment": "python open order",
        "type_time": mt5.ORDER_TIME_SPECIFIED_DAY,
        "type_filling": mt5.ORDER_FILLING_IOC,
        
       # "tp": take_profit
    }

     # send a trading request
    result = mt5.order_send(request)
    print("ticeket",result.order)


    

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("ORDER DONE")      
        print(result)
    
    return result.order

    # send a trading request

   # return result.ticket


def modify_order_tp(ticket, take_profit):

    positions = mt5.positions_get()

    for pos in positions:
        print(pos.ticket)

        if pos.ticket == ticket:
            print("Position found, ticket = ", pos.ticket)
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "tp": take_profit
            }

            order_result = mt5.order_send(request)
            print("order result = \n")
            print(order_result)

            return order_result

    return 'Ticket does not exist'

def check_if_actual_candle_close(symbol,TIMEFRAME,pos_open):

    #check if actual candle is closed
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)
    actual_open = bars_df.iloc[0].open
    

    if actual_open != pos_open:
        print("Closing position on {} because actual candle is closed".format(symbol))
        close_position(symbol,TIMEFRAME)
        return False

    else:
        print("Position is still active on same candle ")


def a (TIMEFRAME):

    if TIMEFRAME == mt5.TIMEFRAME_M1:
            print("M1")
    if TIMEFRAME == "1":
        print("u1u")
    if TIMEFRAME == 1:
        print("1")

def modify_sl(ticket, stop_loss):

    positions = mt5.positions_get()

    for pos in positions:

        if pos.ticket == ticket:
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'symbol': pos.symbol,
                'position': ticket,
                'sl': stop_loss,
                #   'tp': take_profit
               # "magic": 100,
                #"comment": "Modified Stop Loss"
            }

            result = mt5.order_send(request)
            print("STOPLOSS\n",result)


def modify_tp(ticket,take_profit):

    positions = mt5.positions_get()

    for pos in positions:

        if pos.ticket == ticket:
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'symbol': pos.symbol,
                'position': ticket,
                'sl': 0.5,
                'tp': 3.1,
                "comment": "Modified Take Profit"
                #"comment": "Modified Stop Loss"
            }   

            result = mt5.order_send(request)
            print("TAKEPROFIT\n",result)      
    
def modify_sl(ticket, stop_loss,take_profit):


    positions = mt5.positions_get()

    for pos in positions:

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": stop_loss,
                "tp": take_profit,
               # "magic": 100,
                "comment": "Modified Stop Loss"
            }


            result = mt5.order_send(request)

def get_sma():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)
    SMA = bars_df.close.mean()
    return SMA
    

# defining truncate function
# second argument defaults to 0
# so that if no argument is passed
# it returns the integer part of number
 
def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


def isBullish(n):
    open = truncate(bars_df.iloc[n].open,5)
    close = truncate(bars_df.iloc[n].close,5)

    if open <= close:
        return True

    if open > close:
        return False

def isLittleBearish(n):
    openBefore = truncate(bars_df.iloc[n-1].open,5)
    close = truncate(bars_df.iloc[n].close,5)
    highBefore = truncate(bars_df.iloc[n-1].high,5)

    if openBefore >= close:
        return False
    if openBefore + ((highBefore - openBefore)*0.34)< close > SMA:
        return True


def find_3_candles_above_sma():

   
    signal1 = 'flat'
    pattern = 'none'

    if SMA < last_close_3 and isBullish(-4) and isBullish(-3) and isBullish(-2):
        signal1 = 'buy'
        pattern = 'classic'

    # 4 bullish candles in a row and one bearish candle (still bullish)
    if isLittleBearish(-2) and isBullish(-3) and isBullish(-4) and isBullish(-5) and isBullish(-6) and last_close_5 > SMA:
        signal1 = 'buy'
        pattern = '4 bullish'

    # 3 bulish candles in a row and 1 bearish candle and 1 bullish (still bullish) (and bearish candle has close > candle before)
    if isBullish(-2) and isLittleBearish(-3) and isBullish(-4) and isBullish(-5) and isBullish(-6) and last_close_5 > SMA:
        signal1 = 'buy'
        pattern = '3 bullish'

    # 2 bullish candles in a row and one bearish candle and 2 bullish (still bullish)
    if isBullish(-2) and isBullish(-3) and isLittleBearish(-4) and isBullish(-5) and isBullish(-6) and last_open_5 > SMA:
        signal1 = 'buy'
        pattern = '2 bullish'

    print ("### signal1: {}\n pattern: {}".format(signal1,pattern))

def close_position(comment):
    # close all positions on SYMBOL
    if len(positions) > 0:
        for pos in positions:
            # create a close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL,
                "position": pos.ticket,
                "price": mt5.symbol_info_tick(SYMBOL).ask,
                "deviation": 20,
                "magic": 100,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            # send a trading request
            result = mt5.order_send(request)
            if result != None:

                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print("{}\nPosition successfully closed Time ->".format(pos.ticket))
                    return 
    
            else:
                print("{}\nClosing position failed, retcode={} Time -> ".format(pos.ticket, result.retcode))
                return
    else:
        print(SYMBOL, "has no opened positions")
        return

def ma_order():
    tick = mt5.symbol_info_tick(SYMBOL)
     # get OHLC data                             #start pos and #count
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(rates)
    act_open[S] = actual_open

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": VOLUME,
        "type": mt5.ORDER_TYPE_BUY,
       # "price": tick.ask,
        "deviation": DEVIATION,
        "magic": 100,
        "comment": "Market order",
        "type_time": mt5.ORDER_TIME_SPECIFIED_DAY,
        "type_filling": mt5.ORDER_FILLING_IOC,

    # "tp": take_profit
    }

    # send a trading request
    result = mt5.order_send(request)
    print(result)



SYMBO = ["AUDNZD","AUDCAD"]
act_open = [-1] * len(SYMBO)
orders_open = [None] * len(SYMBO)
orders_close =  [None] * len(SYMBO)
ac_open = [-1] * len(SYMBO)
tf = [30] * len(SYMBO)
SMA = 0.0

while True:

    
    for S in range(len(SYMBO)):


        SYMBOL = SYMBO[S]
        VOLUME = 0.01
        TIMEFRAME = mt5.TIMEFRAME_M1
        print("TIMEFRAME",TIMEFRAME)
        SMA_PERIOD = 100
        DEVIATION = 5

        symbol_info = mt5.symbol_info(SYMBOL)
        bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 9)
        bars_df = pd.DataFrame(bars)
        ac_open =bars_df.iloc[0].open

        positions = mt5.positions_get(symbol=SYMBOL)




        signal1,pattern = 'x','x'
        
        actual_price_bid = mt5.symbol_info_tick(SYMBOL).bid
        actual_open = truncate(bars_df.iloc[-1].open,5)
        actual_close = truncate(bars_df.iloc[-1].close,5)
        actual_high = truncate(bars_df.iloc[-1].high,5)
        actual_low = truncate(bars_df.iloc[-1].low,5)
        
        last_open = truncate(bars_df.iloc[-2].open,5)
        last_close = truncate(bars_df.iloc[-2].close,5)
        last_high = truncate(bars_df.iloc[-2].high,5)
        last_low = truncate(bars_df.iloc[-2].low,5)

        last_open_2 = truncate(bars_df.iloc[-3].open,5)
        last_close_2 = truncate(bars_df.iloc[-3].close,5)
        last_high_2 = truncate(bars_df.iloc[-3].high,5)
        last_low_2 = truncate(bars_df.iloc[-3].low,5)

        last_open_3 = truncate(bars_df.iloc[-4].open,5)
        last_close_3 = truncate(bars_df.iloc[-4].close,5)
        last_high_3 = truncate(bars_df.iloc[-4].high,5)
        last_low_3 = truncate(bars_df.iloc[-4].low,5)

        last_open_4 = truncate(bars_df.iloc[-5].open,5)
        last_close_4 = truncate(bars_df.iloc[-5].close,5)
        last_high_4 = truncate(bars_df.iloc[-5].high,5)
        last_low_4 = truncate(bars_df.iloc[-5].low,5)

        last_open_5 = truncate(bars_df.iloc[-6].open,5)
        last_close_5 = truncate(bars_df.iloc[-6].close,5)
        last_high_5 = truncate(bars_df.iloc[-6].high,5)
        last_low_5 = truncate(bars_df.iloc[-6].low,5)




        # get all deals related to the position #530218319

        
        SMA = get_sma()
        
        slippage = 5

    # display EURJPY symbol properties
        symbol_info=mt5.symbol_info(SYMBOL)
        spread = symbol_info.spread
        print (spread,"SPREAD")




        market_order()
        ma_order()

       
       
            #print(position_deals[1])
        

        time.sleep(5)
