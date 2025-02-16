import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time
from termcolor import colored
import sys
import pytz
from time import gmtime, strftime
from decimal import *
import talib
import math

def market_order():

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
        print(ticket[S]," ORDER SUCCESSFULLY PLACED")

    elif result.retcode == mt5.TRADE_RETCODE_MARKET_CLOSED:
        print("MARKET CLOSED")
        time.sleep(3600)

    elif result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS:
        print("Invalid SL on {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
        close_position("Invalid stops")

    else:
        print("ORDER FAILED retcode={} Time -> {}".format(result.retcode,datetime_kyjev.strftime("%H:%M:%S")))

def check_if_price_below_75():

    if actual_high - actual_open >= 9*one_pip:

        stop_los = truncate(actual_open,5)
        if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
            stop_loss[S] = stop_los
            print('{} \nSetting SL on {} to  actual open of candle SL -> {} Time -> {}'.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
            modify_sl(ticket[S])

    if actual_price_bid > actual_open + 9*one_pip:
        stop_los = truncate(((actual_price_bid - actual_open) * 0.786)+actual_open,5)
        if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
            stop_loss[S] = stop_los
            print('{} \nSetting SL on {} to 0.786 SL -> {} Time -> {}'.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
            print("Stop loss in pips is +{}".format(truncate((stop_loss[S] - buy_price)/one_pip,5)))
            modify_sl(ticket[S])
        

    # #if predosla sviecka > 12 pips => SL na 3 pips az pri O+7 pips
    # if last_close - last_open >= 12*one_pip:
    #     if actual_price_bid >= actual_open + 7*one_pip and actual_price_bid < actual_open + 9*one_pip:
    #         stop_los = truncate(actual_open + 3*one_pip,5)
    #         if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
    #             stop_loss[S] = stop_los
    #             print('{} \nSetting SL on {} to  3pips SL -> {} Time -> {}'.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
    #             print("Stop loss in pips is +{}".format(truncate((stop_loss[S] - buy_price)/one_pip,5)))
    #             modify_sl(ticket[S])
    #             return
    #     else :
    #         print("{} Last candle > 12 pips, but actual price < 7 pips on symbol {} Time -> {}".format(ticket[S],SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
    #         return

            
    # #sl = (bid price - buy price)*0.75 + buy price 
    # #if bid price - buy price > 3 pips 
    # #FIBB 0.618 !!!
    # if actual_price_bid - buy_price > 3*one_pip:
    #     stop_los = truncate(buy_price + ((actual_price_bid - buy_price)*0.618),5)
    #     if stop_los != stop_loss[S] and stop_los > stop_loss[S]:
    #         stop_loss[S] = stop_los
    #         print('{} \nSetting SL on {} to  75percent of candle SL -> {} Time -> {}'.format(ticket[S],SYMBOL,stop_loss[S],datetime_kyjev.strftime("%H:%M:%S")))
    #         print("Stop loss in pips is +{}".format(truncate((stop_loss[S] - buy_price)/one_pip,5)))
    #         modify_sl(ticket[S])
    #         return

def check_if_actual_candle_close():
    #if candle is in profit > 10 pips dont close pos 
    if actual_open != act_open[S] and (last_close - last_open) > 10*one_pip:
        #if candle is 10pips+ continue
        print("{} \nCandle is in profit > 10 pips on close, symbol {} Time -> {}".format(ticket[S],SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
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
        print("On {} no opened positions".format(SYMBOL))
  
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
                print("{} \nSL successfully modified {} and TP {}".format(ticket,stop_loss[S],take_profit[S]))


def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

def get_sma():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)
    SMA = truncate(bars_df.close.mean(),5)
    return SMA

def get_sma7():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 7)
    bars_df = pd.DataFrame(bars)
    SMA7 = truncate(bars_df.open.mean(),5)
    return SMA7

def get_sma7minus1():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 1, 7)
    bars_df = pd.DataFrame(bars)
    SMA7minus1 = truncate(bars_df.open.mean(),5)
    return SMA7minus1
    
# check if candle stick low is more than 3 pips below open price
# if yes set take profit to double the distance between open and low
# if no close the position with close candle stick price
def find_stopLoss():
    #zaklad SL bude 6pip
    #ak SMA2.open bude nizsie, az do 9pip taj SMA = SL
    #ak na predoslej sviecke C - O >= 12 pips tak:
        #1.SL podla SMA2 (min 6pip a max 10pip)
        # nastavit na 6 az 9 podla sma2.open
        
    #stop_loss[S] = truncate(actual_open - (6*one_pip),5)

    stop_loss[S] = truncate(Decimal(SMA2Open - 2.5*one_pip),5)

    if stop_loss[S] < actual_open - (12*one_pip):
        stop_loss[S] = truncate(actual_open - (12*one_pip),5)

    SLPips[S] = truncate((actual_open - stop_loss[S])/one_pip,5)
    print('{} SL -> {} SL in pips -> {} Time -> {}'.format(SYMBOL,stop_loss[S],SLPips[S],datetime_kyjev.strftime("%H:%M:%S")))

    # Ak C - O >= 12 pips
    # nastavit na 6 az 9 pips podla sma2.open
    # if (last_close - last_open) >= 12*one_pip:
    #     stop_loss[S] = truncate(SMA2 - 2*one_pip,5)
    #     # Ak SL > 9 tak na 9pips
    #     if stop_loss[S] < actual_open - (9*one_pip):
    #         stop_loss[S] = truncate(actual_open - (9*one_pip),5)
    #         return
    #     # Ak SL < 6 tak na 6pips    
    #     elif stop_loss[S] > actual_open - (6*one_pip):
    #         stop_loss[S] = truncate(actual_open - (6*one_pip),5)
    #         return

    # # if last candle > 12 pips, set stop loss to 0.618 fibb (close - low) close kvoli rezerve
    # if (last_close - last_low) >= 12*one_pip and isBullish(-2):
    #     stop_loss[S] = truncate((last_open + 0.618*(last_close - last_open)),5)

    #     if stop_loss[S] > 9*one_pip:
    #         stop_loss[S] = truncate(actual_open - 9*one_pip,5)
    #     print("{} \nSL set to 0.618 fibb".format(SYMBOL))

    # # stop loss medzi 3 a 9 pips automaticky
    # if (last_open > stop_loss[S]) and (actual_open - last_open) >= 3*one_pip and (actual_open - last_open) < 9*one_pip : 
    #     stop_loss[S] = truncate(last_open,5)
    # elif (actual_open - last_open) < 3*one_pip:
    #     stop_loss[S] = truncate(actual_open - 3*one_pip,5)

    # # ak je last candle bearish tak stop loss je last open 2 alebo open price - 6 pips
    # if (last_open > actual_open):
    #     stop_loss[S] = truncate(last_open_2,5)
    #     if stop_loss[S] <= actual_open - 5*one_pip:
    #         stop_loss[S] = truncate(actual_open - 6*one_pip,5)

    

def check_midnight():
    #check if midnight is passed
    current_datetime = datetime.now()
    hour = current_datetime.hour
    minute = current_datetime.minute
    if hour == 22 and minute == 54:
        for S in range(len(SYMBO)):
            SYMBOLL = SYMBO[S]
            path = 'C:\TradingBot\Log\Log_'+str(strftime("%d_%b_%Y", gmtime()))+'_'+SYMBOLL+'.txt'
            sys.stdout = open(path, 'a')
            #close all positions
            close_all_positions(SYMBOLL)
            print("Midnight is passed")

        time.sleep(3960)
        
        for S in range(len(SYMBO)):
            SYMBOLL = SYMBO[S]
            path = 'C:\TradingBot\Log\Log_'+str(strftime("%d_%b_%Y", gmtime()))+'_'+SYMBOLL+'.txt'
            sys.stdout = open(path, 'a')
            print("Starting after midnight")
            print("Actual time is -> {}".format(datetime.now().strftime("%H:%M:%S")))
            
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
    print("Actual open: ", actual_open)
    print("act_open ", act_open[S])
    print("Actual high: " ,actual_high)
    print("Actual low: ", actual_low)
    print("Actual close: ", actual_close)
    print("Actual price: ", actual_open)
    print("One pip: ", one_pip)
    print("Stop loss: ", stop_loss[S])
    print("Stop loss in pips: ", SLPips[S])
    print("Last open: ", last_open)
    print("Last high: ", last_high)
    print("Last low: ", last_low)
    print("Last close: ", last_close)
    print("SMA100: ",SMA)
    print("SMA100m1: ",SMA100m1)
    print("SMA21",SMA21)
    print("SMA7",SMA7Open)
    print("SMA7m1",SMA7m1)
    print("SMA2",SMA2Open)
    print("SMA2m1",SMA2m1)
    print("Ticket: ", ticket[S])
    print("Spread: ", spread[S])
    print("RSI8: ", RSI8)
    print("RSI8m1: ", RSI8m1)
    print("RSI8m2: ", RSI8m2)
    print("*****************************")
    print("\n")

def findTP():
    if actual_open - actual_price_bid > 3*one_pip:
        tp = truncate((actual_open - actual_price_bid)*2+actual_open,5)
        if tp != take_profit[S] and tp > take_profit[S]:
            take_profit[S] = tp
            print("TP changed to: ", take_profit[S])
            modify_sl(ticket[S])

def check_spread():
    spread[S] = symbol_info.spread
    
    if act_open[S] != actual_open:
        if  spread[S] > 30:
            act_open[S] = actual_open
            print("Spread is too high: {} on {} Time -> {}".format(spread[S],SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return False
        
        else:
            print("Spread is OK: {} on {} Time -> {}".format(spread[S],SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return True

def funct():
    for S in range(len(SYMBO)):
        SYMBOL = SYMBO[S]
        bars = mt5.copy_rates_from_pos(SYMBOL, 30, 0, 2)
        bars_df = pd.DataFrame(bars)     
        act_open[S] = truncate(bars_df.iloc[-1].open,5)

def get_sma2():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 2)
    bars_df = pd.DataFrame(bars)
    SMA1 = bars_df.open.mean()
    return truncate(SMA1,5)

def get_sma100minus1():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 1, 100)
    bars_df = pd.DataFrame(bars)
    SMA100 = bars_df.close.mean()
    return truncate(SMA100,5)
def get_sma100Open():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
    bars_df = pd.DataFrame(bars)
    SMA100 = bars_df.open.mean()
    return truncate(SMA100,5)

def get_sma2m1():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 1, 2)
    bars_df = pd.DataFrame(bars)
    SMA2 = bars_df.open.mean()
    return truncate(SMA2,5)

def get_sma21():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 21)
    bars_df = pd.DataFrame(bars)
    SMA21 = bars_df.close.mean()
    return truncate(SMA21,5)
def get_sma21Open():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 21)
    bars_df = pd.DataFrame(bars)
    SMA21 = bars_df.open.mean()
    return truncate(SMA21,5)
def get_rsi8():
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 8)
    bars_df = pd.DataFrame(bars)
    rsi8 = mt5.RSI(bars_df, 8)
    return truncate(rsi8.iloc[-1],2)

def signal2():
    if actual_open != act_open[S]:
        #buy if SMA2 stupa o 15 pipov a close ma nad SMA100
        #OK
        if Decimal(SMA2Open - SMA2m1) >= 15*one_pip and actual_close > SMA:
            print("BUY#0 Signal2 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return True
        #buy if SMA2 stupa o 25 pipov 
        #OK
        if Decimal(SMA2Open - SMA2m1) >= 25*one_pip:
            print("BUY#1 Signal2 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return True
        #buy if SMA2>SMA7>SMA21 and SMA100>SMA21
        #if SMA2Open > SMA7Open > SMA21 and SMA > SMA21 and isGoingUp(2,"O",30) and isGoingUp(7,"C",30) and isGoingUp(21,"O",30): #pridat UHLY!!!
         #   print("Signal2 BUY#2 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
          #  return True
        #SMA100 nemoze klesat o viac ako 4 points
        #OK
        if Decimal(SMA - SMA100m1) <= -20*one_point:
            act_open[S] = actual_open
            print("Signal2 #1 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return False
        #sma2 musi stupat aspon o 5 pipov
        #OK
        if Decimal(SMA2Open - SMA2m1) < 3.6*one_pip:
            act_open[S] = actual_open
            print("Signal2 #2 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return False 
        #sma2 nemoze stupat o viac ako 25 pipov
        #OK
        if Decimal(SMA2Open - SMA2m1) >= 25*one_pip:
            act_open[S] = actual_open
            print("Signal2 #2.1 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return False
        #open - pip > SMA2 
        #OK
        if actual_open + 1*one_pip < SMA2Open:
            act_open[S] = actual_open
            print("Signal2 #3 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return False
        #open - SMA7 < 30 pipov
        # if Decimal(actual_open - SMA7Open) > 30*one_pip:
        #     act_open[S] = actual_open
        #     print("Signal2 #4 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
        #     return False
        #SMA7 musi stupat aspon o 1.5 pipu (1 pip je malo
        #OK
        if Decimal(SMA7Open - SMA7m1) < 15*one_point:
            act_open[S] = actual_open
            print("Signal2 #5 on symbol {} SMA7m1 {} Time -> {}".format(SYMBOL,SMA7m1,datetime_kyjev.strftime("%H:%M:%S")))
            return False
        #vsetky SMA musia byt bullish a open musi byt najvyssie
        if SMA2Open > SMA7Open > SMA and actual_open > SMA7Open:
            print("BUY#3 Signal2 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return True
        #ak prejde vsetky 
        act_open[S] = actual_open


def signal3():
    #ak je O-L > H-O tak cakat sviecku
    #pridat ak je C < O !!!
    if act_open[S] != actual_open:
        if last_open - last_low >= last_high - last_open:
            if act_open[S] != actual_open:
                act_open[S] = actual_open
                print("Signal3 #1")
                return False
        else :
            print("BUY Signal3 #0 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return True
    
def signal4():
    if act_open[S] != actual_open:
        #SMA2 a SMA7 na 4H TF musia byt bullish
        if isGoingUp(2,"O",16388) and isGoingUp(7,"O",16388) and SMA2Open >= SMA100Open and SMA7Open >= SMA100Open:
            print("BUY Signal4 #0 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return True
        else:
            print("Signal4 #1 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            act_open[S] = actual_open
            return False
    
def signal5():
    if act_open[S] != actual_open:
        #SMA2,7 a 21 musia byt bullish na 30M TF
        if isGoingUp(2,"O",30) and isGoingUp(7,"O",30) and isGoingUp(21,"O",30) and SMA2Open > SMA7Open > SMA21Open:
            print("BUY Signal5 #0 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            return True
        else:
            print("Signal5 #1 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
            act_open[S] = actual_open
            return False
#RSI
def signal6():
    if act_open[S] != actual_open:
        
        if RSI8 < 75:
            rsiStop[S] = False        
            print("rsiStop = ",rsiStop[S])

        #Uhol klesa a RSI8 >= 75, buy az pod 75
        if RSI8 - RSI8m1 < RSI8m1-RSI8m2 and RSI8 >= 75:
            print("Signal6 #2 on symbol {} RSI8 {} RSI8m1 {} RSI8m2 {} Time -> {}".format(SYMBOL,RSI8,RSI8m1,RSI8m2,datetime_kyjev.strftime("%H:%M:%S")))
            rsiStop[S] = True
            act_open[S] = actual_open
            return False
        #rsi go down 
        if RSI8 < RSI8m1 :
            print("Signal6 #1 on symbol {} RSI8 {} RSI8m1 {} RSI8m2 {} Time -> {}".format(SYMBOL,RSI8,RSI8m1,RSI8m2,datetime_kyjev.strftime("%H:%M:%S")))
            act_open[S] = actual_open
            return False


        
        if rsiStop[S] == False:
            print("BUY Signal6 #3 on symbol {} RSI8 {} RSI8m1 {} RSI8m2 {} Time -> {}".format(SYMBOL,RSI8,RSI8m1,RSI8m2,datetime_kyjev.strftime("%H:%M:%S")))
            return True  
        else:
            print("Signal6 #4 on symbol {} RSI8 {} RSI8m1 {} RSI8m2 {} Time -> {}".format(SYMBOL,RSI8,RSI8m1,RSI8m2,datetime_kyjev.strftime("%H:%M:%S")))
            act_open[S] = actual_open
            return False

def signal7():
    #ak je sma7 mensia ako SMA7-2 az SMA7-9 tak nekupovat
    if act_open[S] != actual_open:
        for x in range(1,10,1):
            prevSMA = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, x, 7)
            prevSMA_df = pd.DataFrame(prevSMA)
            prevSMA7 = truncate(prevSMA_df.open.mean(),5)

            if prevSMA7 >= SMA7Open:
                print("Signal7 #1 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
                act_open[S] = actual_open
                return False
            
        print("BUY Signal7 #0 on symbol {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))
        return True
    



#SMA je klesajuca alebo stupajuca
def isGoingUp(LENGHT,TYPE,TIMEFRAME):
    """SMA100 a SMA7 je close SMA2 a SMA21 je open\n4H TF = 16388"""
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, LENGHT)
    bars_df = pd.DataFrame(bars)
    SMA = 0
    if TYPE == "O":
        SMA = bars_df.open.mean()

    elif TYPE == "C":
        SMA = bars_df.close.mean()
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 1, LENGHT)
    bars_df = pd.DataFrame(bars) 
    SMAm1 = 0
    if TYPE == "O":
        SMAm1 = bars_df.open.mean()
    elif TYPE == "C":
        SMAm1 = bars_df.close.mean()
    if SMA > SMAm1:
        return True
    else:
        return False
    



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
rsiStop = [True] * len(SYMBO)

getcontext().prec = 8

while True:
    for S in range(len(SYMBO)):

        path = 'C:\TradingBot\Log\Log_'+str(strftime("%d_%b_%Y", gmtime()))+'_'+SYMBO[S]+'.txt'
        sys.stdout = open(path, 'a')
        
        tz_kyjev = pytz.timezone('Europe/Kirov')
        datetime_kyjev = datetime.now(tz_kyjev)

        SYMBOL = SYMBO[S]
        TIMEFRAME = mt5.TIMEFRAME_M30
        VOLUME = 0.2
        SMA_PERIOD = 100
        DEVIATION = 20
        SMA = 0.0
        one_pip = (mt5.symbol_info(SYMBOL).point)*10
        one_point = mt5.symbol_info(SYMBOL).point
        # get OHLC data                             #start pos and #count
        bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
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
        
        elif actual_open != act_open[S]:
            SMA = get_sma()
            SMA100m1 = get_sma100minus1()
            SMA100Open = get_sma100Open() 
            SMA2Open = get_sma2()
            SMA2m1 = get_sma2m1()
            SMA7Open = get_sma7()
            SMA7m1 = get_sma7minus1()
            SMA21 = get_sma21()
            SMA21Open = get_sma21Open()
            open_prices = bars['open']
            relativeStrenghtIndex = talib.RSI(open_prices, timeperiod=8)
            RSI8 = round_up(relativeStrenghtIndex[-1],2)
            RSI8m1 = round_up(relativeStrenghtIndex[-2],2)
            RSI8m2 = round_up(relativeStrenghtIndex[-3],2)

            #signal1,pattern = find_3_candles_above_sma()
            spreadIsLow = check_spread()
            s2 = signal2()
            s3 = signal3()
            s4 = signal4()
            s5 = signal5()
            s6 = signal6()
            s7 = signal7()
            if s2 == True:
                print("S2", s2)
            if s3 == True:
                print("S3", s3)
            if s4 == True:
                print("S4", s4)
            if s5 == True:
                print("S5", s5)
            if s6 == True:
                print("S6", s6)
                print("ACT open and actual open = {} and {} on symbol {}".format(act_open[S], actual_open, SYMBOL))
            if  s7 == True:
                print("S7", s7)

            if  (act_open[S] != actual_open) == True and spreadIsLow == True and s2 == True and s3 == True and s4 == True and s5 == True and s6 == True and s7 == True:
                print("S2 S3 S4 S5 S6 are TRUE")
                find_stopLoss()
                market_order()
                print_everything()
                take_profit[S] = 0.0

    else:
        time.sleep(1)
