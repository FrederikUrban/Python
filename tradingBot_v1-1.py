import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time
from termcolor import colored


# function to send a market order


def market_order(symbol, VOLUME, DEVIATION, stop_loss):
    tick = mt5.symbol_info_tick(symbol)
     # get OHLC data                             #start pos and #count
    #rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 1)
   # bars_df = pd.DataFrame(bars)

    #find open price of candle
   
    


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
    order = result.order

    # send a trading request

    return result,order

def close_order(ticket):
    positions = mt5.positions_get()

    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        # 0 represents buy, 1 represents sell - inverting order_type to close the position
        type_dict = {0: 1, 1: 0}
        price_dict = {0: tick.ask, 1: tick.bid}

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": type_dict[pos.type],
                "price": price_dict[pos.type],
                "deviation": DEVIATION,
                "magic": 100,
                "comment": "python close order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,

            }

            close_order_result = mt5.order_send(request)
            if close_order_result.retcode == mt5.TRADE_RETCODE_DONE:
                print("ORDER SUCCESSFULLY CLOSED")
            else:
                print("ORDER FAILED retcode={}".format(close_order_result.retcode))
            
            return close_order_result

    return 'Ticket does not exist'

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
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 4)
    bars_df = pd.DataFrame(bars)
    ac_close = bars_df.iloc[-1].close
    last_close = bars_df.iloc[-2].close
    last_close_2 = bars_df.iloc[-3].close
    last_close_3 = bars_df.iloc[-4].close
    print("actual close is {} last close is {} last close 2 is {} last close 3 is {}".format(ac_close ,last_close, last_close_2, last_close_3))

    signal1 = 'flat'
    if sma < last_close_3 < last_close_2 <  last_close < ac_close:
        signal1 = 'buy'
    elif last_close < sma:
        print('last close is below sma or last close is bellow last close 2\n')
        signal1 = 'flat'
    
    return signal1, sma, last_close, last_close_2, last_close_3

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
        if (last_close - last_open) < (last_high - last_open)*0.5:
            #wait for next candle open
            return False
        else:
            return True

# check if candle stick low is more than 3 pips below open price
# if yes set take profit to double the distance between open and low
# if no close the position with close candle stick price
def find_stopLoss(symbol, TIMEFRAME):
        # get OHLC data                             #start pos and #count
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 2)
    bars_df = pd.DataFrame(rates)

    # get open price of the first candle
    open_price = bars_df.iloc[-1].open
    one_pip = (mt5.symbol_info(symbol).point)*10
    last_close = bars_df.iloc[-1].close
    last_open = bars_df.iloc[-2].open
    print('last close is {} and last open is {}'.format(last_close,last_open))

    #stop loss is -15 pips from open price
    stop_loss = open_price - (15*one_pip)

    #if last close is higher than stop loss set stop loss to last close
    if last_open > stop_loss:
        stop_loss = last_open
    
   
    


    return stop_loss, open_price

def check_if_act_price_is_above_last_open(symbol, TIMEFRAME):
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 2)
    bars_df = pd.DataFrame(rates)

    last_open = bars_df.iloc[-2].open
    actual_price = get_price(symbol)

    print('last open is {} and actual price is {}'.format(last_open,actual_price))

    if actual_price > last_open:
        return True
    else:
        return False
        print('actual price is below last open')

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

    print('**************actual low is {} and actual open is {}'.format(actual_low,actual_open))


    if actual_low < actual_open - one_pip*take_profit_diff:
        take_profit = (actual_open - actual_low)*risk_to_reward + actual_open
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
            print(order_result)

            return order_result

    return 'Ticket does not exist'

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
            print(colored('**************modify sl to {}**************'.format(stop_loss), 'red'))
            order_result = mt5.order_send(request)
            print(order_result)

            return order_result

    return 'Ticket does not exist'

#get sma
def get_sma(symbol, TIMEFRAME, SMA_PERIOD):
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)
    sma = bars_df.close.mean()
    return sma

def check_if_active_order(orders):

    if orders == None:
        print("Orders are closed on {}".format(SYMBOL))
        active_order = False
        return active_order
    else:
        print("Order still active on ", SYMBOL)
        active_order = True
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
    
            #set stop loss to   (actual_high - actual_open)*0.75
            stop_loss = actual_open + (actual_high - actual_open)*0.75
            print(colored('price is below 75%' , 'cyan'))
            print('stop loss is {}'.format(actual_price-stop_loss))
            modify_sl(ticket, stop_loss)
            return stop_loss

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
            print("1. close position #{}: sell {} {} lots at {} with deviation={} points".format(pos.ticket, ssymbol, pos.volume, mt5.symbol_info_tick(ssymbol).ask, 20))
            # check the execution result
            print("2. order_send(): by {} {} lots at {} with deviation={} points done, ".format(ssymbol, pos.volume, mt5.symbol_info_tick(ssymbol).ask, 20), result)
    else:
        print(ssymbol, "has no opened positions")

def check_if_actual_candle_close(symbol,TIMEFRAME,pos_open):

    #check if actual candle is closed
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)
    bars_df = pd.DataFrame(bars)
    actual_open = bars_df.iloc[0].open
    
    print('actual open:{} and pos_open {}'.format(actual_open,pos_open))

    if actual_open != pos_open:
        close_position(symbol)
        print('close position(actual open != pos_open)')
        return False

    else:
        print("pozicie sa rovnaju")
        return True
        
def print_stopLoss_takeProfit(result,stop_loss):
   
    open_pos_price = result.price
    
    print("RESULT {}\n stop loss={}".format(result, open_pos_price-stop_loss))

# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
else:
    print("initialize() success")

while True:
    if __name__ == '__main__':

        SYMBOL = "NZDJPY"
        VOLUME = 1.0
        TIMEFRAME = mt5.TIMEFRAME_M5
        SMA_PERIOD = 100
        DEVIATION = 20
        symbol_info = mt5.symbol_info(SYMBOL)
        bars = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 1)
        bars_df = pd.DataFrame(bars)
        act_open = bars_df.iloc[-1].open
        order = mt5.orders_get(symbol=SYMBOL)

        print('Actual open is {}'.format(act_open))
        
        
        sma = get_sma(SYMBOL, TIMEFRAME, SMA_PERIOD)
        
        #spread
        exposure = get_exposure(SYMBOL)
        print("Exposure is {}".format(exposure))

        # checking for first trading signal
        signal1, sma, last_close, last_close2, last_close3 = find_3_candles_above_sma(SYMBOL, TIMEFRAME,sma)
        print('Signal = {} last close is {} last close 2 is {} last close 3 is {} sma is {}\n'.format(signal1,last_close, last_close2, last_close3, sma))

        #BUYING
        if signal1 == 'buy':
            print(colored('buy signal', 'green'))
        
            # check if there is an active order
            active_order = display_data(SYMBOL)
            #check if last candle has a wick bigger than 50% of candle body
            candle_wick_is_bigger = check_last_candle_wick(SYMBOL, TIMEFRAME)
            print("candle_wick_is_bigger than 50%_of body: ")
            if candle_wick_is_bigger == True:
                print(colored('True', 'green'))
            else:
                print(colored('False', 'red'))
            #check if actual price is above last open
            act_price_is_above_last_open = check_if_act_price_is_above_last_open(SYMBOL, TIMEFRAME)
            
            print("active_order is ")
            if active_order == True:
                print(colored(active_order, 'red'))
            else:
                print(colored(active_order, 'green'))

            print("act_price_is_above_last_open")
            if act_price_is_above_last_open == True:
                print(colored('True', 'green'))
            else:
                print(colored('False', 'red'))
           
                     

            if active_order == False and candle_wick_is_bigger == True and act_price_is_above_last_open == True:

                stop_loss ,act_open = find_stopLoss(SYMBOL, TIMEFRAME,)
                print("stop loss is {}  and ACT_OPEN IS {}".format(stop_loss,act_open))
                #make market order and return result order id and open price of candle
                result,order = market_order(SYMBOL, VOLUME, DEVIATION,stop_loss)
                print('result, act_open,order')
                print_f(result, act_open,order)
                

                print("active order is ----------")
                print(colored(active_order, 'yellow'))
                
                print_stopLoss_takeProfit(result,stop_loss)

            while active_order:
                print(colored('Order is active' , 'green'))
                #set take profit and stop loss
                take_profit = set_takeProfit(SYMBOL, TIMEFRAME)
                time.sleep(1)
                print("take profit is {}".format(take_profit))
                if take_profit > 0:
                            # modify order
                            modify_order(order, take_profit)
                #close position if price is below 75% of actual candle
                check_if_price_below_75(SYMBOL, TIMEFRAME,order)
                #close position if actual candle is closed
                active_order = check_if_actual_candle_close(SYMBOL, TIMEFRAME,act_open)
                if active_order == False:
                    break
                # checking if order is still active
                active_order= check_if_active_order(order)
            
                #price = get_price(SYMBOL)
        else: 
            print(colored('Not BUY' , 'red'))

        #close order with order id
        #close_order_result = close_order(order)

        


    ##get actual open price of candle
    ## rates_df = pd.DataFrame(rates)
    ##print("OpenPRICE is {}  ".format(open_long))

        time.sleep(1)

    ##print("shutdown success")
    #mt5.shutdown()