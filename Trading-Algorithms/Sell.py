import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time
from termcolor import colored
import sys
from datetime import datetime
import pytz

# function to send a market order


def market_order(symbol, VOLUME, DEVIATION, stop_loss,TIMEFRAME):
    tick = mt5.symbol_info_tick(symbol)
     # get OHLC data                             #start pos and #count
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(rates)
    ac_open = bars_df.iloc[0].open

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": VOLUME,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "deviation": DEVIATION,
        "magic": 100,
        "comment": "python open order",
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
        close_position(symbol)
        
    else:
        print(colored("ORDER FAILED retcode={}".format(result.retcode), 'red'))

    result_price = result.price

    return ac_open,result_price


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
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 5)
    bars_df = pd.DataFrame(bars)
    last_close = bars_df.iloc[-2].close
    last_close_2 = bars_df.iloc[-3].close
    last_close_3 = bars_df.iloc[-4].close
    last_open_3 = bars_df.iloc[-4].open

   
    signal1 = 'flat'
    if sma < last_close_3 < last_close_2 <  last_close and last_open_3 < last_close_3 :
        signal1 = 'buy'
        
    
   

    return signal1
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
        else:
            return True

# check if candle stick low is more than 3 pips below open price
# if yes set take profit to double the distance between open and low
# if no close the position with close candle stick price
def find_stopLoss(symbol, TIMEFRAME):
        # get OHLC data                             #start pos and #count
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 2)
    bars_df = pd.DataFrame(rates)

    # get open price of the first candle
    open_price = bars_df.iloc[-1].open
    one_pip = (mt5.symbol_info(symbol).point)*10
   
    last_open = bars_df.iloc[-2].open

    #stop loss is -15 pips from open price
    stop_loss = open_price - (15*one_pip)

    #if last close is higher than stop loss set stop loss to last close
    if last_open > stop_loss:
        stop_loss = last_open
    
    print('stop loss is {}'.format(stop_loss))

    return stop_loss

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

#find low of actual candle and set take profit
def set_takeProfit(symbol, TIMEFRAME):
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 2)
    bars_df = pd.DataFrame(bars)

    take_profit = 0
    take_profit_diff = 3
    risk_to_reward = 2
    one_pip = (mt5.symbol_info(symbol).point)*10
    actual_low = bars_df.iloc[-1].low
    actual_open = bars_df.iloc[-1].open

    if actual_low < actual_open - one_pip*take_profit_diff:
        take_profit = (actual_open - actual_low)*risk_to_reward + actual_open
        print('Setting takeProfit to {}'.format(take_profit))
    else:
        print('Did not set takeProfit')
    
    return take_profit

def modify_order(ticket, take_profit):

    positions = mt5.positions_get()

    for pos in positions:

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "magic": 100,
                "tp": take_profit
            }

            order_result = mt5.order_send(request)
            if (order_result.retcode == mt5.TRADE_RETCODE_DONE):
                #print time
                print("Modified takeProfit to {}".format(take_profit))
            else:
                print("Failed to modify take profit, retcode={}".format(order_result.retcode))

            return order_result

    print(colored('Ticket does not exist'))

def modify_sl(ticket, stop_loss):

    positions = mt5.positions_get()

    for pos in positions:

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "magic": 100,
                "sl": stop_loss
            }

            order_result = mt5.order_send(request)

            if (order_result.retcode == mt5.TRADE_RETCODE_DONE):
                print("Modified stop loss to 75percent of  candle {}".format(stop_loss))
            else:
                print("Failed to modify stop loss to 75percent of candle, retcode={}".format(order_result.retcode))



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
        actual_price = mt5.symbol_info_tick(symbol).bid
        one_pip = (mt5.symbol_info(symbol).point)*10

        #close position only if actual price is at least 3 pips above open price
        if actual_price > actual_open + 3*one_pip:
            
            print('Stoploss = to 75percent of candle')
            #set stop loss to   (actual_high - actual_open)*0.75
            stop_loss = actual_open + ((actual_high - actual_open)*0.75)
           
            modify_sl(ticket, stop_loss)


def close_position(ssymbol):
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
                "comment": "python script close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            # send a trading request
            result = mt5.order_send(request)
            close_price = result.price
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print("1 position #{} closed".format(pos.ticket))
                return close_price
    
            else:
                print("1 close position #{} failed, retcode={}".format(pos.ticket, result.retcode))
    else:
        print(ssymbol, "has no opened positions")

def check_if_actual_candle_close(symbol,TIMEFRAME,pos_open):

    #check if actual candle is closed
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)
    actual_open = bars_df.iloc[0].open
    

    if actual_open != pos_open:
        print("Closing position on {} because actual candle is closed".format(symbol))
        close_price = close_position(symbol)
        return True, close_price

        
    else:
        print("Position is still active on same candle ")
        return False, 0

        
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

def pips10_profit_candle(orders_open,orders_close, symbol,TIMEFRAME,tf):
    #if ac candle close with profit greater than 10 pips
    #set time frame to 5 min
    symbol_info = mt5.symbol_info(symbol)
    bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)

    digits = symbol_info.digits
    if digits == 5:
        a = 10000
    elif digits == 3:
        a = 1000
    elif digits == 2:
        a = 100
    else :
        print("SOMETHINGS WRONG")

    pip = 10*mt5.symbol_info(symbol).point

    if tf == 30:
        if ((orders_close - orders_open)*a) > 10*pip:
            ac_open = bars_df.iloc[-1].open
            print("profit is greater than 10 pips | TimeFrame changed to 5 min|")
            return ac_open, mt5.TIMEFRAME_M5
        else:
            print("profit is not greater than 10 pips | TimeFrame is 30 min|")
            return 0, mt5.TIMEFRAME_M30
    else:
        print("TimeFrame is 5 min")
        return 0, mt5.TIMEFRAME_M30

def print_everything(symbol, TIMEFRAME, stop_loss,takeprofit ):

    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)

    actual_open = bars_df.iloc[0].open
    actual_high = bars_df.iloc[0].high
    actual_low = bars_df.iloc[0].low
    actual_close = bars_df.iloc[0].close
    actual_price = mt5.symbol_info_tick(symbol).ask
    one_pip = (mt5.symbol_info(symbol).point)*10


    print("*****************************")
    print("Time: ", datetime_kyjev.strftime("%H:%M:%S"))
    print("Timeframe: ", TIMEFRAME)
    print("Symbol: ", symbol)
    print("Actual open: ", actual_open)
    print("Actual high: ", actual_high)
    print("Actual low: ", actual_low)
    print("Actual close: ", actual_close)
    print("Actual price: ", actual_price)
    print("One pip: ", one_pip)
    print("Stop loss: ", stop_loss)
    print("take profit: ", takeprofit)
    print("*****************************")




########################################################################################


path = 'C:\TradingBot\Log\log.txt'
sys.stdout = open(path, 'w')







# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
else:
    print("initialize() success")

SYMBO = ["AUDNZD","AUDUSD","CADCHF","CADJPY","CHFJPY","EURAUD","EURCAD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD","EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD","NZDCAD","AUDCHF","AUDJPY","NZDUSD","USDCAD","USDCHF","USDJPY","AUDCAD"]

act_open = [-1] * len(SYMBO)
orders_open = [0] * len(SYMBO)
#orders_close =  [None] * len(SYMBO)
ac_open_on_close = [-1] * len(SYMBO)
tf = [mt5.TIMEFRAME_M30] * len(SYMBO)
stop_loss = [0] * len(SYMBO)


while True:


    for S in range(len(SYMBO)):

        tz_kyjev = pytz.timezone('Europe/Kiev')
        datetime_kyjev = datetime.now(tz_kyjev)

        SYMBOL = SYMBO[S]

        if tf[S] == "5":
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

        if ac_open_on_close[S] == bars_df.iloc[-7].open:
            tf[S] = mt5.TIMEFRAME_M30
            print("Setting timeframe back to 30 min")

        if len(positions) > 0:
            
            ticket = positions[0].ticket
            actual_price = mt5.symbol_info_tick(SYMBOL).ask

            if stop_loss[S] > actual_price:
                print("Stop loss is greater than actual price")
                print("Closing position")
                close_position(SYMBOL)
                print_everything(SYMBOL, TIMEFRAME, "None", "None")
                break

            #MODIFIED

            #set take profit and stop loss
            take_profit = set_takeProfit(SYMBOL, TIMEFRAME)
            if take_profit > 0:
                        # modify order
                        modify_order(ticket, take_profit)

            #close position if price is below 75% of actual candle
            check_if_price_below_75(SYMBOL, TIMEFRAME,ticket)
            #close position if actual candle is closed
            
            print("act_open is {}".format(act_open[S]))

            closed_candle ,close_price = check_if_actual_candle_close(SYMBOL, TIMEFRAME,act_open[S])
            if closed_candle == True:
                ac_open_on_close[S],tf[S] = pips10_profit_candle(orders_open[S], close_price, SYMBOL, TIMEFRAME, tf[S])


            print_everything(SYMBOL, TIMEFRAME, "None", take_profit)
            # checking if order is still active

            ####


        else:

            active_order = False
            
            sma = get_sma(SYMBOL, TIMEFRAME, SMA_PERIOD)

            # print("SMA is {}".format(sma))

            #spread
            exposure = get_exposure(SYMBOL)
            # print("Exposure is {}".format(exposure))

            # checking for first trading signal
            signal1 = find_3_candles_above_sma(SYMBOL, TIMEFRAME,sma)

            #BUYING
            if signal1 == 'buy':
                
            
                #check if last candle has a wick bigger than 50% of candle body
                candle_wick_is_bigger = check_last_candle_wick(SYMBOL, TIMEFRAME)
                if candle_wick_is_bigger == True:
                    print(colored('candle_wick_is_bigger than 50%', 'green'))
                else:
                    print(colored('candle_wick_is_NOT_bigger than 50%', 'red'))

                #check if actual price is above last open
                #act_price_is_above_last_open = check_if_act_price_is_above_last_open(SYMBOL, TIMEFRAME)

            
            
                
                        

            if candle_wick_is_bigger == True and signal1 == 'buy' and act_open[S] != bars_df.iloc[-1].open:

                    stop_loss[S] = find_stopLoss(SYMBOL, TIMEFRAME)
                    
                    #make market order and return result order id and open price of candle
                    act_open[S],orders_open[S] = market_order(SYMBOL, VOLUME, DEVIATION,stop_loss[S],TIMEFRAME)

                    print("Do act_open sa ulozilo: {}".format(act_open[S]))
                    
                    print_everything(SYMBOL, TIMEFRAME, stop_loss[S], "None")
            
    if S == len(SYMBO)-1:
        time.sleep(1)
