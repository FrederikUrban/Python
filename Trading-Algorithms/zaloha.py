import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time
from termcolor import colored
import sys
import pytz
from time import gmtime, strftime
#aaaa
def market_order():
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
        "sl": stop_loss[S],
    # "tp": take_profit
    }

    # send a trading request
    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        ticket[S] = result.order
        print(colored(ticket[S]," ORDER SUCCESSFULLY PLACED" , 'yellow'))

    elif result.retcode == mt5.TRADE_RETCODE_MARKET_CLOSED:
        print(colored("MARKET CLOSED", 'red'))
        time.sleep(3600)

    elif result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS:
        print("Invalid SL on {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
        close_position("Invalid stops")

    else:
        print("ORDER FAILED retcode={} Time -> {}".format(result.retcode,datetime_kyjev.strftime("%H:%M:%S")))


def check_if_price_below_75():

    #sl = (bid price - buy price)*0.75 + buy price 
    #FIBB 0.618 !!!
    if actual_price_bid - buy_price > 3*one_pip:
        stop_los = truncate(buy_price + ((actual_price_bid - buy_price)*0.618),5)
        if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
            stop_loss[S] = stop_los
            print('{} \nSetting SL on {} to  75percent of candle SL -> {} Time -> {}'.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
            print("Stop loss in pips is +{}".format(truncate((stop_loss[S] - buy_price)/one_pip,5)))
            modify_sl(ticket[S])
            return





    
    # nasobok = 0.5
    # pips = 0
    
    # if actual_price_bid > actual_open:

    #     while pips + actual_open < actual_price_bid:
    #         pips += one_pip
    #         nasobok += 0.04
    #         if nasobok >= 0.9:
    #             break
        
    #     stop_los = truncate(actual_open + (nasobok * (actual_high - actual_open)),5)
    #     if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
    #         stop_loss[S] = stop_los
    #         print('{} \nSetting SL on {} to  {} percent of candle SL -> {} Time -> {}'.format(ticket[S],SYMBOL,nasobok*100,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
    #         print("Stop loss in pips is {}".format(truncate((actual_high - stop_loss[S])/one_pip,5)))
    #         modify_sl(ticket[S])
    #         return

        # if actual_price_bid >= actual_open + 6*one_pip:
        #     #set stop loss to   (actual_high - actual_open)*0.75
        #     stop_los = truncate(actual_open + ((actual_high - actual_open)*0.75),5)
        #     if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
        #         stop_loss[S] = stop_los
        #         print('{} \nSetting SL on {} to  75percent of candle SL -> {} Time -> {}'.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
        #         print("Stop loss in pips is {}".format(truncate((actual_high - stop_loss[S])/one_pip,5)))
        #         modify_sl(ticket[S])
        #         return

        # if actual_price_bid >= actual_open + 4*one_pip:
        #     #set stop loss to   actual price + 1 pip
        #     stop_los = truncate(actual_open + one_pip,5)
        #     if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
        #         stop_loss[S] = stop_los
        #         print('{} \nSetting SL on {}, 1 pip above open, SL -> {} Time -> {}'.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
        #         print("Stop loss in pips is {}".format(truncate((actual_high - stop_loss[S])/one_pip,5)))
        #         modify_sl(ticket[S])
        #         return

        # if actual_price_bid >= actual_open + 3*one_pip:
        #     #set stop loss to  actual price
        #     stop_los = truncate(actual_open,5)
        #     if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
        #         stop_loss[S] = stop_los
        #         print('{} \nSetting SL on {}, to actual open, SL -> {} Time -> {} '.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
        #         print("Stop loss in pips is {}".format(truncate((actual_high - stop_loss[S])/one_pip,5)))
        #         modify_sl(ticket[S])
        #         return

def check_if_actual_candle_close():
    #if candle is in profit > 10 pips dont close pos 
    if actual_open != act_open[S] and (last_close - last_open) > 10*one_pip:
        #if candle is 10pips+ continue
        act_open[S] = actual_open
        return

    if actual_open != act_open[S]:
        print("{} \nClosing position on {} , because actual candle is closed, act_open {}, actual open {} Time -> {}".format(ticket[S],SYMBOL,act_open[S],actual_open,datetime_kyjev.strftime("%H:%M:%S")))
        close_position("actual candle is closed")

def close_all_positions(SYMBOL):
    # close all positions on SYMBOL
    position = mt5.positions_get()
    if len(position) > 0:
        for pos in position:
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
                "comment": "CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            # send a trading request
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print("{} \nPosition successfully closed Time -> {}".format(pos.ticket,datetime_kyjev.strftime("%H:%M:%S")))
            else:
                print("{} \nClosing position failed, retcode={} Time -> {}".format(pos.ticket, result.retcode,datetime_kyjev.strftime("%H:%M:%S")))
    else:    
        print("No opened positions")
        

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
                    print("{}\nPosition successfully closed Time -> {}".format(pos.ticket,datetime_kyjev.strftime("%H:%M:%S")))
                    return 
    
            else:
                print("{}\nClosing position failed, retcode={} Time -> {}".format(pos.ticket, result.retcode,datetime_kyjev.strftime("%H:%M:%S")))
                return
    else:
        print(SYMBOL, "has no opened positions")
        return


def modify_sl(ticket):
    positions = mt5.positions_get()

    for pos in positions:
        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "SYMBOL": pos.symbol,
                "position": ticket,
                "sl": stop_loss[S],
                "tp": take_profit[S],
                "comment": "Modified Stop Loss"
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("{} \nSL or TP faild to modify, retcode={}".format(ticket,result.retcode))
            else:
                print("{} \nSL successfully modified to 75 percent of candle {} and TP {}".format(ticket,stop_loss[S],take_profit[S]))

def setSL_ifNewCandle():
    if stop_loss[S] < actual_open - 6*one_pip:
        find_stopLoss()
        modify_sl (ticket[S])

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier
    
def get_sma():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)
    SMA = bars_df.close.mean()
    return SMA
    

# check if candle stick low is more than 3 pips below open price
# if yes set take profit to double the distance between open and low
# if no close the position with close candle stick price
def find_stopLoss():
    stop_loss[S] = truncate(actual_open - (10*one_pip),5)

    # if last candle > 12 pips, set stop loss to 0.618 fibb (close - low) close kvoli rezerve
    if (last_close - last_low) >= 12*one_pip and isBullish(-2):
        stop_loss[S] = truncate((last_open + 0.618*(last_close - last_open)) - spread[S]*one_pip,5)
        print("{} \nSL set to 0.618 fibb".format(SYMBOL))

    # stop loss medzi 3 a 12 pips automaticky
    if (last_open > stop_loss[S]) and (actual_open - last_open) >= 3*one_pip and (actual_open - last_open) < 12*one_pip : 
        stop_loss[S] = truncate(last_open,5)
    elif (actual_open - last_open) < 3*one_pip:
        stop_loss[S] = truncate(actual_open - 3*one_pip,5)

    # ak je last candle bearish tak stop loss je last open 2 alebo open price - 6 pips
    if (last_open > actual_open):
        stop_loss[S] = truncate(last_open_2,5)
        if stop_loss[S] <= actual_open - 5*one_pip:
            stop_loss[S] = truncate(actual_open - 6*one_pip,5)

    SLPips[S] = truncate((actual_open - stop_loss[S])/one_pip,5)
    print('{} SL -> {} SL in pips -> {} Time -> {}'.format(SYMBOL,stop_loss[S],SLPips[S],datetime_kyjev.strftime("%H:%M:%S")))

def check_midnight():
    #check if midnight is passed
    current_datetime = datetime.now()
    hour = current_datetime.hour
    minute = current_datetime.minute
    if hour == 22 and minute == 54:
        for S in range(len(SYMBO)):
            SYMBOLL = SYMBO[S]
            print("Midnight is passed")
            #close all positions
            close_all_positions(SYMBOLL)
        
        time.sleep(3600)
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            quit()
        else:
            print("initialize() success")
        

# this strategy will open a long position if the last 3 candles have close prices above the simple moving average
def find_3_candles_above_sma():

   
    signal1 = 'flat'
    pattern = 'none'

    if SMA < last_close_3 and isBullish(-4) and isBullish(-3) and isBullish(-2):
        signal1 = 'buy'
        pattern = 'classic'
        

    # 4 bullish candles in a row and one bearish candle (still bullish)
    elif isLittleBearish(-2) and isBullish(-3) and isBullish(-4) and isBullish(-5) and isBullish(-6) and last_close_5 > SMA:
        signal1 = 'buy'
        pattern = '4 bullish'

    # 3 bulish candles in a row and 1 bearish candle and 1 bullish (still bullish) (and bearish candle has close > candle before)
    elif isBullish(-2) and isLittleBearish(-3) and isBullish(-4) and isBullish(-5) and isBullish(-6) and last_close_5 > SMA:
        signal1 = 'buy'
        pattern = '3 bullish'

    # 2 bullish candles in a row and one bearish candle and 2 bullish (still bullish)
    elif isBullish(-2) and isBullish(-3) and isLittleBearish(-4) and isBullish(-5) and isBullish(-6) and last_open_5 > SMA:
        signal1 = 'buy'
        pattern = '2 bullish'

    #pridat 3 bullish 1 bear 1 bull  1 bear (Este otestovat)

    return signal1,pattern

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
    if (openBefore + ((highBefore - openBefore)*0.34)) < close and close > SMA:
        return True

def print_everything():

    print("*****************************")
    print("Time: ", datetime_kyjev.strftime("%H:%M:%S"))
    print("Timeframe: ", TIMEFRAME)
    print("Symbol: ", SYMBOL)
    print("Actual open: ", truncate(actual_open,5))
    print("Actual high: ", truncate(actual_high,5))
    print("Actual low: ", truncate(actual_low,5))
    print("Actual close: ", truncate(actual_close,5))
    print("Actual price: ", truncate(actual_open,5))
    print("One pip: ", one_pip)
    print("Stop loss: ", truncate(stop_loss[S],5))
    print("Stop loss in pips: ", truncate(SLPips[S],5))
    print("Last open: ", truncate(last_open,5))
    print("Last high: ", truncate(last_high,5))
    print("Last low: ", truncate(last_low,5))
    print("Last close: ", truncate(last_close,5))
    print("SMA: ", truncate(SMA,5))
    print("Pattern: ", pattern)
    print("ticket: ", ticket[S])
    print("*****************************")
    print("\n")

def findTP():
    if actual_open - actual_price_bid > 3*one_pip:
        tp = truncate(((actual_open - actual_price_bid)*2)+actual_open,5)
        if tp != take_profit[S] and tp > take_profit[S]:
            take_profit[S] = tp
            print("TP changed to: ", take_profit[S])
            modify_sl(ticket[S])

def check_spread():
    spread[S] = symbol_info.spread
    if spread[S] <= 15:
        return True
    elif act_open[S] != actual_open:
        act_open[S] = actual_open
        print("Spread is too high: {} on {} Time -> {}".format(spread[S],SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
        return False

def funct():
    for S in range(len(SYMBO)):
        SYMBOL = SYMBO[S]
        bars = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M30, 0, 2)
        bars_df = pd.DataFrame(bars)     
        act_open[S] = truncate(bars_df.iloc[-1].open,5)



path = 'C:\TradingBot\Log\Log_'+str(strftime("%d_%b_%Y-%H_%M", gmtime()))+'.txt'
sys.stdout = open(path, 'w')

# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
else:
    print("initialize() success")

SYMBO = ["AUDNZD","AUDUSD","CADCHF","CADJPY","CHFJPY","EURAUD","EURCAD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD","EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD","NZDCAD","AUDCHF","AUDJPY","NZDUSD","USDCAD","USDCHF","USDJPY","AUDCAD"]

#akutalne hodnoty pre act price
global act_open
act_open = [0.0] * len(SYMBO)
funct()

orders_open = [0.0] * len(SYMBO)
#orders_close =  [None] * len(SYMBO)
act_open_on_close = [0.0] * len(SYMBO)
tf = [mt5.TIMEFRAME_M30] * len(SYMBO)
stop_loss = [0.0] * len(SYMBO)
take_profit = [0.0] * len(SYMBO)
order = [0] * len(SYMBO)
pattern = 0
profit = [0.0] * len(SYMBO)
OKlast5min = [True] * len(SYMBO)
OKlast5minSavedOpenPrice = [0.0] * len(SYMBO)
ticket = [0] * len(SYMBO)
SLPips = [0.0] * len(SYMBO)
spread = [0] * len(SYMBO)

while True:
    for S in range(len(SYMBO)):

        tz_kyjev = pytz.timezone('Europe/Kiev')
        datetime_kyjev = datetime.now(tz_kyjev)

        SYMBOL = SYMBO[S]
        TIMEFRAME = mt5.TIMEFRAME_M30
        VOLUME = 0.2
        SMA_PERIOD = 100
        DEVIATION = 20
        SMA = 0.0
        one_pip = (mt5.symbol_info(SYMBOL).point)*10
        # get OHLC data                             #start pos and #count
        bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 8)
        bars_df = pd.DataFrame(bars)     
        
        symbol_info=mt5.symbol_info(SYMBOL)
        



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



        check_midnight()

        positions = mt5.positions_get(symbol=SYMBOL)

            
        
        if len(positions) > 0:
            profit = positions[0].profit
            ticket[S] = positions[0].ticket
            buy_price = truncate(positions[0].price_open,5)
            #setSL_ifNewCandle()
            check_if_price_below_75()
            check_if_actual_candle_close()
            findTP()
        
        else:
            SMA = get_sma()
            signal1,pattern = find_3_candles_above_sma()
            spreadIsLow = check_spread()

            if signal1 == 'buy' and act_open[S] != actual_open and spreadIsLow :
                find_stopLoss()
                market_order()
                print_everything()
                take_profit[S] = 0.0

    if S == len(SYMBO):
        time.sleep(1)
