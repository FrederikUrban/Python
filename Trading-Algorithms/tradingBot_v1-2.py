import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time
from termcolor import colored
import sys
from datetime import datetime
import pytz
from time import gmtime, strftime
# function to send a market order


def market_order(symbol, VOLUME, DEVIATION, stop_loss,TIMEFRAME):
    tick = mt5.symbol_info_tick(symbol)
     # get OHLC data                             #start pos and #count
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(rates)
    ac_open = truncate(bars_df.iloc[0].open,5)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": VOLUME,
        "type": mt5.ORDER_TYPE_BUY,
       # "price": tick.ask,
        "deviation": DEVIATION,
        "magic": 100,
        "comment": "Market order",
        "type_time": mt5.ORDER_TIME_SPECIFIED_DAY,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "sl": stop_loss,
    # "tp": take_profit
    }

    # send a trading request
    result = mt5.order_send(request)
    
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        
        print(colored("ORDER SUCCESSFULLY PLACED" , 'yellow'))
        print("Actual open is ",ac_open)

    elif result.retcode == mt5.TRADE_RETCODE_MARKET_CLOSED:
        print(colored("MARKET CLOSED", 'red'))
        time.sleep(3600)
    elif result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS:
        print(colored("INVALID STOPS on symbol {}".format(symbol), 'red'))
        close_position(symbol,"Invalid stops")
        
    else:
        print(colored("ORDER FAILED retcode={}".format(result.retcode), 'red'))

    result_price = result.price

    return ac_open,truncate(result_price,5),result.order


def get_price(SYMBOL):
    symbol_info = mt5.symbol_info(SYMBOL)
    return symbol_info.ask

def print_f(result, open_price,order):
    print("Retcode is {} open_price is {} and order is {}".format(result.retcode,open_price,order))
    if result.retcode == mt5.TRADE_RETCODE_NO_MONEY:
        print("No money")
    elif result.retcode == mt5.TRADE_RETCODE_DONE:
        print(colored("ORDER SUCCESSFULLY PLACED"))
    elif result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS:
        print("Invalid stop loss")
    else:
        print("Order failed, retcode={}".format(result.retcode))

# function to get the exposure of a symbol
def get_exposure(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        pos_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
        exposure = pos_df['volume'].sum()

        return exposure

# this strategy will open a long position if the last 3 candles have close prices above the simple moving average
def find_3_candles_above_sma(symbol, TIMEFRAME, sma):
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 7)
    bars_df = pd.DataFrame(bars)
    last_close = bars_df.iloc[-2].close
    last_close_2 = bars_df.iloc[-3].close
    last_high_2 = bars_df.iloc[-3].high
    last_open_2 = bars_df.iloc[-3].open

    last_close_3 = bars_df.iloc[-4].close
    last_open_3 = bars_df.iloc[-4].open
    last_high_3 = bars_df.iloc[-4].high 

    last_close_4 = bars_df.iloc[-5].close
    last_close_5 = bars_df.iloc[-6].close
    last_open_5 = bars_df.iloc[-6].open
    last_close_6 = bars_df.iloc[-7].close
   
    signal1 = 'flat'
    pattern = 'none'

    if sma < last_close_3 < last_close_2 <  last_close and last_open_3 < last_close_3 :
        signal1 = 'buy'
        pattern = 'classic'

    # 4 bullish candles in a row and one bearish candle (still bullish)
    if last_close_2 >last_close_3 > last_close_4 > last_close_5 > last_open_5 > sma and last_close > ((last_high_2 - last_open_2)*0.34 + last_open_2) > sma:
        signal1 = 'buy'
        pattern = '4 bullish'
    # 3 bulish candles in a row and one bearish candle and 1 bullish (still bullish) (and bearish candle has close > candle before)
    if last_close_3 > last_close_4  > last_close_5 > last_open_5 > sma and last_close > last_close_2 > sma and last_close_2 > last_close_3:
        signal1 = 'buy'
        pattern = '3 bullish'
    # 2 bullish candles in a row and one bearish candle and 2 bullish (still bullish)
    if  last_close_4 > last_close_5 > last_open_5 > sma and last_close > last_close_2 > last_close_3 > sma:
        signal1 = 'buy'
        pattern = '2 bullish'
   

    return signal1,pattern
# display data on active orders on symbol
def display_data(ssymbol):
    
    postions = mt5.positions_get(symbol = ssymbol)
    print("Zadany symbol je ")
    print(colored(ssymbol, 'magenta'))

    if len(postions) == 0:
        print(colored('No positions on' ,'red' ))
        print(ssymbol)
        active_position = False
    else:
        print("Total positions on :")
        print(colored(len(postions), 'blue'))
        # display all active positions
        for pos in postions:
            print(pos)
        active_position = True
    return active_position

#check if last candle has a wick bigger than 50% of candle body
def check_last_candle_wick(symbol, TIMEFRAME):
    
        bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 2)
        bars_df = pd.DataFrame(bars)
    
        last_open = bars_df.iloc[0].open
        last_close = bars_df.iloc[0].close
        last_high = bars_df.iloc[0].high
        one_pip = (mt5.symbol_info(symbol).point)*10
    
        #if last candle has a wick bigger than 50% of candle body
        if (last_close - last_open) <= (last_high - last_open)*0.5:
            #wait for next candle open
            return False
        elif (last_close < last_open):
            return True
        else:
            return True

# check if candle stick low is more than 3 pips below open price
# if yes set take profit to double the distance between open and low
# if no close the position with close candle stick price
def find_stopLoss(symbol, TIMEFRAME):
        # get OHLC data                             #start pos and #count
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 3)
    bars_df = pd.DataFrame(rates)
    # get open price of the first candle
    open_price = bars_df.iloc[-1].open
    one_pip = (mt5.symbol_info(symbol).point)*10
    last_open = bars_df.iloc[-2].open
    last_open_2 = bars_df.iloc[-3].open

    stop_loss = open_price - (15*one_pip)

    # stop loss medzi 6 a 15 pips automaticky
    if (last_open > stop_loss) and (open_price - last_open) >= 6*one_pip and (open_price - last_open) < 15*one_pip : 
        stop_loss = last_open
    elif (open_price - last_open) < 6*one_pip:
        stop_loss = open_price - 6*one_pip

    # ak je last candle bearish tak stop loss je last open 2 alebo open price - 6 pips
    if (last_open > open_price):
        stop_loss = last_open_2
        if stop_loss <= open_price - 5*one_pip:
            stop_loss = open_price - 6*one_pip


    print('stop loss je vypocitany na {}'.format(stop_loss))

    cPips = (open_price - stop_loss)*one_pip

    return truncate(stop_loss,5),cPips

def check_if_act_price_is_above_last_open(symbol, TIMEFRAME):
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 2)
    bars_df = pd.DataFrame(rates)

    last_open = bars_df.iloc[-2].open
    actual_price = get_price(symbol)

    print('last open is {} and actual price is {}'.format(last_open,actual_price))

    if actual_price > last_open:
        return True
    else:
        print('actual price is below last open')
        return False


def modify_order(ticket, take_profit,stop_loss):

    positions = mt5.positions_get()

    for pos in positions:

        if pos.ticket == ticket:
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'position': pos.ticket,
                'symbol': pos.symbol,
                'tp': take_profit,
                'sl': stop_loss,
                'comment': 'Modified Take Profit and sl'
            }

            order_result = mt5.order_send(request)
            print('Setting takeProfit to {}'.format(take_profit))
        #    if (order_result.retcode == mt5.TRADE_RETCODE_DONE):
                #print time
         #       print("Modified takeProfit to {}".format(take_profit))
          #  else:
           #     print("Failed to modify take profit, retcode={}".format(order_result.retcode))

            return order_result

    print(colored('Ticket does not exist'))

def modify_sl(ticket, stop_loss):


    positions = mt5.positions_get()

    for pos in positions:

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": stop_loss,
                #"tp": take_profit,
               # "magic": 100,
                "comment": "Modified Stop Loss"
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("[F] Stoploss order failed, retcode={}".format(result.retcode))
            else:
                print("[S] Modified stop loss to 75 percent of candle {}".format(stop_loss))



#get sma
def get_sma(symbol, TIMEFRAME, SMA_PERIOD):
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)
    sma = bars_df.close.mean()
    return sma

def check_if_active_order(SYMBOL):
    ac_order = mt5.orders_get(symbol = SYMBOL)

    if len(ac_order) > 0:
        print("Order still active on ", SYMBOL)
        active_order = True
        return active_order

    else:
        print("Orders are closed on {}".format(SYMBOL))
        active_order = False
        return active_order

#check if actuall price of candle is above 75% of actual candle
def check_if_price_below_75(symbol, TIMEFRAME,ticket):

        bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0,1)
        bars_df = pd.DataFrame(bars)

        actual_open = bars_df.iloc[0].open
        actual_high = bars_df.iloc[0].high
        actual_price_bid = mt5.symbol_info_tick(symbol).bid
        one_pip = (mt5.symbol_info(symbol).point)*10

        if actual_price_bid >= actual_open + 6*one_pip:
            #set stop loss to   (actual_high - actual_open)*0.75
            stop_los = truncate(actual_open + ((actual_high - actual_open)*0.75),5)
            if stop_los != stop_loss[S]:
                stop_loss[S] = stop_los
                print('Setting stoploss on {} to  75percent of candle | {} |'.format(symbol,stop_loss[S]))
                print("Stop loss in pips is {}".format(truncate((actual_high - stop_loss[S])*one_pip),5))
                modify_sl(ticket, stop_los)
                return

        if actual_price_bid >= actual_open + 4*one_pip:
            #set stop loss to   actual price + 1 pip
            stop_los = truncate(actual_open + one_pip,5)
            if stop_los != stop_loss[S]:
                stop_loss[S] = stop_los
                print('Setting stoploss on {}, 1 pip above open  | {} |'.format(symbol,stop_loss[S]))
                print("Stop loss in pips is {}".format(truncate((actual_high - stop_loss[S])*one_pip),5))
                modify_sl(ticket, stop_los)
                return

        if actual_price_bid >= actual_open + 3*one_pip:
            #set stop loss to  actual price
            stop_los = truncate(actual_open,5)
            if stop_los != stop_loss[S]:
                stop_loss[S] = stop_los
                print('Setting stoploss on {} to  actual open | {} |'.format(symbol,stop_loss[S]))
                print("Stop loss in pips is {}".format(truncate((actual_high - stop_loss[S])*one_pip),5))
                modify_sl(ticket, stop_los)
                return



def close_position(ssymbol, comment):
    # close all positions on symbol
    symbol_positions = mt5.positions_get(symbol=ssymbol)
    if len(symbol_positions) > 0:
        for pos in symbol_positions:
            # create a close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": ssymbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL,
                "position": pos.ticket,
                "price": mt5.symbol_info_tick(ssymbol).ask,
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
                    print("1 position #{} closed".format(pos.ticket))
                    return 
    
            else:
                print("1 close position #{} failed, retcode={}".format(pos.ticket, result.retcode))
                return
    else:
        print(ssymbol, "has no opened positions")
        return

def check_if_actual_candle_close(symbol,TIMEFRAME,pos_open,ticket):

    #check if actual candle is closed
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)
    actual_open = truncate(bars_df.iloc[0].open,5)
    
    #if candle is in profit > 10 pips dont close pos 
    if actual_open != pos_open:
        #get profit 
        positions=mt5.positions_get(symbol=SYMBOL)
        if positions==None:
            print("No positions on USDCHF, error code={}".format(mt5.last_error()))
        elif len(positions)>0:
            print("Total positions on {} = {}".format(SYMBOL,len(positions)))

            profit = positions[0].profit
            print("Profit = ",profit)

            if profit > 80:
                act_open[S] = actual_open
  

        



    if actual_open != pos_open:
        print("Closing position on {} with ticket {}, because actual candle is closed".format(symbol,ticket))
        close_position(symbol,"actual candle is closed")



        
def print_stopLoss_takeProfit(result,stop_loss):
   
    open_pos_price = result.price
    
    print("RESULT {}\n stop loss={}".format(result, open_pos_price-stop_loss))

def only_one_order_per_candle_is_active(act_open,symbol,TIMEFRAME):
    #check if actual candle is closed
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)
    actual_open = bars_df.iloc[0].open
    
    if actual_open == act_open:
        print("actual open is {} and act_open is {}".format(actual_open,act_open))
        return True
    else:
        print("actual open is {} and act_open is {}".format(actual_open,act_open))
        return False

def pips10_profit_candle(symbol,TIMEFRAME,tf,profit):
    #if ac candle close with profit greater than 10 pips
    #set time frame to 5 min
    symbol_info = mt5.symbol_info(symbol)
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)

    if tf == 30:
        if profit >= 100:
            ac_open = truncate(bars_df.iloc[-1].open,5)
            print("profit is greater than 100 $ | TimeFrame changed to 5 min|")
            return ac_open, mt5.TIMEFRAME_M5
        else:
            print("profit is not greater than 100 $ | TimeFrame is 30 min|")
            return 0, mt5.TIMEFRAME_M30
    else:
        print("TimeFrame is still 5 min")
        return 0, mt5.TIMEFRAME_M30

def print_everything(symbol, TIMEFRAME, stop_loss,takeprofit,ticket,pattern ):

    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)

    actual_open = bars_df.iloc[0].open
    actual_high = bars_df.iloc[0].high
    actual_low = bars_df.iloc[0].low
    actual_close = bars_df.iloc[0].close
    actual_price = mt5.symbol_info_tick(symbol).ask
    one_pip = (mt5.symbol_info(symbol).point)*10
    last_open = bars_df.iloc[-1].open
    last_high = bars_df.iloc[-1].high
    last_low = bars_df.iloc[-1].low
    last_close = bars_df.iloc[-1].close


    print("*****************************")
    print("Time: ", datetime_kyjev.strftime("%H:%M:%S"))
    print("Timeframe: ", TIMEFRAME)
    print("Symbol: ", symbol)
    print("Actual open: ", truncate(actual_open,5))
    print("Actual high: ", truncate(actual_high,5))
    print("Actual low: ", truncate(actual_low,5))
    print("Actual close: ", truncate(actual_close,5))
    print("Actual price: ", truncate(actual_price,5))
    print("One pip: ", one_pip)
    print("Stop loss: ", truncate(stop_loss,5))
    print("Stop loss in pips: ", truncate((actual_open - stop_loss)*10,5))
    print("take profit: ", takeprofit)
    print("Last open: ", truncate(last_open,5))
    print("Last high: ", truncate(last_high,5))
    print("Last low: ", truncate(last_low,5))
    print("Last close: ", truncate(last_close,5))
    print("SMA: ", truncate(sma,5))
    print("Pattern: ", pattern)
    print("ticket: ", ticket)
    print("*****************************")
    print("\n")

def check_last5min():
    #check if last 5 min candle is bearish
    bars = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 2)
    bars_df = pd.DataFrame(bars)
    last_open = bars_df.iloc[-2].open
    last_close = bars_df.iloc[-2].close
    last_high = bars_df.iloc[-2].high
    actual_open = truncate(bars_df.iloc[-1].open,5)
    
    #stop for 30 min if last 5 min candle is bearish
    if last_open > last_close:
        print("Last 5 min candle is bearish")
        return False, actual_open
    else:
        return True, actual_open

def check_midnight():
    #check if midnight is passed
    current_datetime = datetime.now()
    hour = current_datetime.hour
    minute = current_datetime.minute
    if hour == 00 and minute == 54:
        print("Midnight is passed")
        #close all positions
        for i in range(len(SYMBO)):
            close_position(SYMBO[i])
            print("#AllPos Closing position on symbol: ", SYMBO[i])
            time.sleep(3600)


# defining truncate function
# second argument defaults to 0
# so that if no argument is passed
# it returns the integer part of number
 
def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier
 


def check_lastCandle():
    #check if last 5 min candle is closed
    bars = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M30, 0, 2)
    bars_df = pd.DataFrame(bars)
    last_open = bars_df.iloc[-2].open
    last_close = bars_df.iloc[-2].close
    one_pip = (mt5.symbol_info(SYMBOL).point)*10
    actual_open = truncate(bars_df.iloc[-1].open,5)
    last_high = bars_df.iloc[-2].high
    last_low = bars_df.iloc[-2].low

    if (last_high - last_open)*one_pip >= 12*one_pip or (last_open - last_low) >= 12*one_pip:
        print("Last 30 min candle > 12 pips")
        tf[S] = mt5.TIMEFRAME_M5
        return actual_open
    else:
        return 0.0
        
    
def setSL_ifNewCandle():
    bars = mt5.copy_rates_from_pos(SYMBOL,TIMEFRAME, 0, 2)
    bars_df = pd.DataFrame(bars)
    last_open = truncate(bars_df.iloc[-2].open,5)

    if stop_loss[S] < last_open:
        stop_loss[S] , cPips = find_stopLoss(SYMBOL,TIMEFRAME)
        modify_sl (ticket, stop_loss[S])





########################################################################################

from datetime import datetime
  
# get current date and time


path = 'C:\TradingBot\Log\Log_'+str(strftime("%d_%b_%Y-%H_%M", gmtime()))+'.txt'

sys.stdout = open(path, 'w')


# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
else:
    print("initialize() success")

SYMBO = ["AUDNZD","AUDUSD","CADCHF","CADJPY","CHFJPY","EURAUD","EURCAD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD","EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD","NZDCAD","AUDCHF","AUDJPY","NZDUSD","USDCAD","USDCHF","USDJPY","AUDCAD"]

act_open = [0.0] * len(SYMBO)
orders_open = [0.0] * len(SYMBO)
#orders_close =  [None] * len(SYMBO)
ac_open_on_close = [0.0] * len(SYMBO)
tf = [mt5.TIMEFRAME_M30] * len(SYMBO)
stop_loss = [0.0] * len(SYMBO)
take_profit = [0.0] * len(SYMBO)
order = [0] * len(SYMBO)
pattern = 0
profit = [0.0] * len(SYMBO)
OKlast5min = [True] * len(SYMBO)
OKlast5minSavedOpenPrice = [0.0] * len(SYMBO)

while True:


    for S in range(len(SYMBO)):

        tz_kyjev = pytz.timezone('Europe/Kiev')
        datetime_kyjev = datetime.now(tz_kyjev)


        SYMBOL = SYMBO[S]

        if tf[S] == 5:
            TIMEFRAME = mt5.TIMEFRAME_M5
            print("Setting timeframe to 5 min")
        else:
            TIMEFRAME = mt5.TIMEFRAME_M30
        

        VOLUME = 1.0
        SMA_PERIOD = 100
        DEVIATION = 20
        #symbol_info = mt5.symbol_info(SYMBOL)
        bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 8)
        bars_df = pd.DataFrame(bars)
        active_order = False
        #actual_open = bars_df.iloc[-1].open
        candle_wick_is_bigger = False

        
        positions = mt5.positions_get(symbol=SYMBOL)

        if ac_open_on_close[S] == truncate(bars_df.iloc[-7].open,5):
            tf[S] = mt5.TIMEFRAME_M30
            print("Setting timeframe back to 30 min")
        
        #check if last 5 min candle is below 50% of candle if yes, no trade for 30 min and then reset OKlast5min
        if OKlast5min[S] == False:
            if tf[S] == 30:
                if OKlast5minSavedOpenPrice[S] != truncate(bars_df.iloc[-1].open,5):
                    OKlast5min[S] = True
                    print("Re-Setting OKlast5min to True")
            elif tf[S] == 5:
                if OKlast5minSavedOpenPrice[S] == truncate(bars_df.iloc[-7].open,5):
                    OKlast5min[S] = True
                    print("Re-Setting OKlast5min to True")


        check_midnight()

        if len(positions) > 0:
            
            ticket = positions[0].ticket

            setSL_ifNewCandle()
            
            #MODIFIED
            
            #close position if price is below 75% of actual candle
            #!!!!
            #!!!!
            # !!!!
            # !!!!
            # nastavit stop loss aby ho nehitlo hned     
            check_if_price_below_75(SYMBOL, TIMEFRAME,ticket)
            #close position if actual candle is closed
            
            check_if_actual_candle_close(SYMBOL, TIMEFRAME,act_open[S],ticket)

            ####


        else:

            active_order = False
            
            sma = get_sma(SYMBOL, TIMEFRAME, SMA_PERIOD)

            # print("SMA is {}".format(sma))

            #spread
            exposure = get_exposure(SYMBOL)
            # print("Exposure is {}".format(exposure))

            # checking for first trading signal
            signal1,pattern = find_3_candles_above_sma(SYMBOL, TIMEFRAME,sma)


            #Change timeframe if last candle > 12 pips
            if tf[S] == 30:
                ac_open_on_close[S] = check_lastCandle()
                TIMEFRAME = tf[S]


            

            #check last 5 min on candle if was bearish
           
           # OKlast5min[S],OKlast5minSavedOpenPrice[S] = check_last5min()
              
                


            #BUYING
            if signal1 == 'buy':
               candle_wick_is_bigger = True 
                #check if last candle has a wick bigger than 50% of candle body
                #candle_wick_is_bigger = check_last_candle_wick(SYMBOL, TIMEFRAME)

            if candle_wick_is_bigger == True and signal1 == 'buy' and act_open[S] != truncate(bars_df.iloc[-1].open,5):
                # and OKlast5min[S] == True:

                    stop_loss[S],cPips = find_stopLoss(SYMBOL, TIMEFRAME)
                    
                    #make market order and return result order id and open price of candle
                    act_open[S],orders_open[S],order[S] = market_order(SYMBOL, VOLUME, DEVIATION,stop_loss[S],TIMEFRAME)

                    
                    print_everything(SYMBOL, TIMEFRAME, stop_loss[S], "None",order[S],pattern)
            
    if S == len(SYMBO)-1:
        time.sleep(1)
