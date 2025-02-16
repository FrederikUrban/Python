import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time


# function to send a market order
def market_order(symbol, VOLUME, DEVIATION,stop_loss):
    tick = mt5.symbol_info_tick(symbol)

    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)

    open_longCandle =  bars_df.iloc[0].open

   # order_dict = {'buy': 0, 'sell': 1}
   # price_dict = {'buy': tick.ask, 'sell': tick.bid}

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
    print(result.return_code)
    order = result.order

    # check the execution result
  #  print("1. order_send(): by {} {} lots at {} with deviation={} points".format(SYMBOL,VOLUME,tick.ask,DEVIATION));
  #  if order_result.retcode != mt5.TRADE_RETCODE_DONE:
   #    print("2. order_send failed, retcode={}".format(order_result.retcode))
    #    # request the result as a dictionary and display it element by element
     #   result_dict=order_result._asdict()
      #  for field in result_dict.keys():
       #     print("   {}={}".format(field,result_dict[field]))
        #    # if this is a trading request structure, display it element by element as well
         #   if field=="request":
          #      traderequest_dict=result_dict[field]._asdict()
           #     for tradereq_filed in traderequest_dict:
            #        print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
        #print("shutdown() and quit")
        #mt5.shutdown()
        #quit()
    


    return result,open_longCandle,order

# function to close an order base don ticket id
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

            order_result = mt5.order_send(request)
            print(order_result)

            return order_result

    return 'Ticket does not exist'

# function to get the exposure of a symbol
def get_exposure(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        pos_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
        exposure = pos_df['volume'].sum()

        return exposure

# function to look for trading signals
def signal(symbol, timeframe, sma_period):
    bars = mt5.copy_rates_from_pos(symbol, timeframe, 1, sma_period)
    bars_df = pd.DataFrame(bars)

    last_close = bars_df.iloc[-1].close
    sma = bars_df.close.mean()

    direction = 'flat'
    if last_close > sma:
        direction = 'buy'
    elif last_close < sma:
        direction = 'sell'

    return last_close, sma, direction

# this strategy will open a long position if the last 3 candles have close prices above the simple moving average
def find_3_candles_above_sma(symbol, TIMEFRAME, SMA_PERIOD):
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)

    last_close = bars_df.iloc[-1].close
    last_close_2 = bars_df.iloc[-2].close
    last_close_3 = bars_df.iloc[-3].close

    sma = bars_df.close.mean()

    signal1 = 'flat'
    if last_close_3 > sma and last_close_2 > sma and last_close_2 > last_close_3 and last_close > sma and last_close > last_close_2:
        signal1 = 'buy'
    elif last_close < sma:
        print('last close is below sma or last close is bellow last close 2\n')
        signal1 = 'flat'

    return signal1, sma, last_close, last_close_2, last_close_3

# check if candle stick low is more than 3 pips below open price
# if yes set take profit to double the distance between open and low
# if no close the position with close candle stick price
def find_stopLoss(symbol, TIMEFRAME, SMA_PERIOD):
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)

   
    one_pip = (mt5.symbol_info(symbol).point)*10
    last_close = bars_df.iloc[-1].close
    act_open = bars_df.iloc[0].open

    #stop loss is -15 pips from open price
    stop_loss = act_open - (15*one_pip)

    #if last close is higher than stop loss set stop loss to last close
    if last_close > stop_loss:
        stop_loss = last_close

    return stop_loss,act_open

#find low of actual candle and set take profit
def set_takeProfit(symbol, TIMEFRAME, SMA_PERIOD):
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)

    take_profit = 0
    take_profit_diff = 3
    risk_to_reward = 2
    one_pip = (mt5.symbol_info(symbol).point)*10
    actual_low = bars_df.iloc[0].low
    actual_open = bars_df.iloc[0].open

    if actual_low < actual_open - take_profit_diff*one_pip:
        take_profit = (actual_open - actual_low)*risk_to_reward
   
    print('actual low: \n', actual_low)
    print('take profit: \n', take_profit)
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

# display data on active orders on symbol
def display_data(symbol,active_order):
    
    orderz=mt5.orders_get(symbol)

    if orderz is None:
        print("No orders on", symbol ," error code={}".format(mt5.last_error()))
        active_order = False

    else:
        print("Total orders on ",symbol,": ",len(orderz))
        # display all active orders
        for orderz in orderz:
            print(orderz)
        active_order = True

    return active_order

def check_if_active_order(symbol,active_order):
    orderz=mt5.orders_get(symbol)

    if orderz is None:
        print("Order closed on ", symbol ," error code={}".format(mt5.last_error()))
        active_order = False
        return active_order

#check if actuall price of candle is above 75% of actual candle
def check_if_price_below_75(symbol, TIMEFRAME, SMA_PERIOD):

        bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, SMA_PERIOD)
        bars_df = pd.DataFrame(bars)

        actual_open = bars_df.iloc[0].open
        actual_high = bars_df.iloc[0].high
        actual_price = mt5.symbol_info_tick(symbol).ask
        one_pip = (mt5.symbol_info(symbol).point)*10

        #close position only if actual price is at least 3 pips above open price
        if actual_price > actual_open + 3*one_pip:
            #check if actual price is below 75% of actual candle
            if (actual_price - actual_open) < (actual_high - actual_open)*0.75:
                    #close position
                    print('close position\n')
                    close_position(symbol)
                    return False
                   

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
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            # send a trading request
            result = mt5.order_send(request)
            print("1. close position #{}: sell {} {} lots at {} with deviation={} points".format(pos.ticket, ssymbol, pos.volume, mt5.symbol_info_tick(ssymbol).ask, 20))
            # check the execution result
            print("2. order_send(): by {} {} lots at {} with deviation={} points done, ".format(ssymbol, pos.volume, mt5.symbol_info_tick(ssymbol).ask, 20), result)
    else:
        print(ssymbol, "has no opened positions")

def check_if_actual_candle_close(symbol,TIMEFRAME,SMA_PERIOD,pos_open):

    #check if actual candle is closed
    bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, SMA_PERIOD)
    bars_df = pd.DataFrame(bars)
    actual_open = bars_df.iloc[0].open
    
    if actual_open != pos_open:
        close_position(symbol)

#check if last candle has a wick bigger than 50% of candle body
def check_last_candle_wick(symbol, TIMEFRAME, SMA_PERIOD):
    
        bars = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, SMA_PERIOD)
        bars_df = pd.DataFrame(bars)
    
        last_open = bars_df.iloc[1].open
        last_close = bars_df.iloc[1].close
        last_high = bars_df.iloc[1].high
        one_pip = (mt5.symbol_info(symbol).point)*10
    
        #if last candle has a wick bigger than 50% of candle body
        if (last_close - last_open) < (last_high - last_open)*0.5:
            #wait for next candle open
            return False
        else:
            return True


if __name__ == '__main__':

    # strategy parameters
    ss = ["EURCHF","EURGBP","EURUSD","GBPUSD","USDCHF","USDJPY","AUDUSD","NZDUSD","USDCAD","EURCAD","EURJPY","GBPJPY","AUDCAD","AUDJPY","AUDNZD","CADCHF","CADJPY","CHFJPY","EURAUD","GBPAUD","GBPCAD","GBPCHF","NZDCAD","NZDCHF","NZDJPY"]
   

    
    #  mt5.initialize()

    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()

   
  

    while True:


        for SYMBOL in range(len(ss)):
            print('symbol is ',[ss[SYMBOL]])
           
               
            
            VOLUME = 1.0
            TIMEFRAME = mt5.TIMEFRAME_M1
            SMA_PERIOD = 100
            DEVIATION = 20
            tick = mt5.symbol_info_tick(ss[SYMBOL])
            symbol_info = mt5.symbol_info(ss[SYMBOL])
            active_order = False
            open_longCandle = 0

            bars = mt5.copy_rates_from_pos(ss[SYMBOL], TIMEFRAME, 1, SMA_PERIOD)
            bars_df = pd.DataFrame(bars)

         #   actual_open = bars_df.iloc[0].open
          #  pip = mt5.symbol_info(SYMBOL).point*10
           # print('actual open is ',actual_open,'and pip is ',pip,'and stop loss is ',actual_open - 15*pip,' (',actual_open,' - ',pip*15,')')

            print("Checking for symbol: \n",ss[SYMBOL])

           # stop_loss,act_open = find_stopLoss(SYMBOL, TIMEFRAME, SMA_PERIOD)

            #print('actual open is ',act_open,'and stop loss is ',stop_loss)

            # calculating account exposure
            exposure = get_exposure(ss[SYMBOL])

            # checking for first trading signal
            signal1, sma, last_close, last_close2, last_close3 = find_3_candles_above_sma(ss[SYMBOL], TIMEFRAME, SMA_PERIOD)

            # trading logic
            if signal1 == 'buy':

                # check if there is an active order
                active_order = display_data(ss[SYMBOL],active_order)
                #check if last candle has a wick bigger than 50% of candle body
                candle_wick_is_bigger = check_last_candle_wick(ss[SYMBOL], TIMEFRAME, SMA_PERIOD)
                # if we have a BUY signal, open a long position
                print("candle_wick_is_bigger: \n", candle_wick_is_bigger)
                

                if active_order == False and candle_wick_is_bigger == True:
                    stop_loss = find_stopLoss(ss[SYMBOL], TIMEFRAME, SMA_PERIOD)
                    # make buy market execution order
                    order_result,open_longCandle,order_id = market_order(ss[SYMBOL], VOLUME, DEVIATION, stop_loss)
                    print("---order_result: \n", order_result,'----')
                    #open position of actual candle
                    pos_open = bars_df.iloc[0].open
                    print("position_id: \n", order_id)
                    active_order = True
                    

                while active_order:
                    # set take profit and stop loss
                    take_profit = set_takeProfit(ss[SYMBOL], TIMEFRAME, SMA_PERIOD)
                    if take_profit > 0:
                        # modify order
                        modify_order(order_id, take_profit)

                    #close position if price is below 75% of actual candle
                    active_order = check_if_price_below_75(ss[SYMBOL], TIMEFRAME, SMA_PERIOD)
                    #close position if actual candle is closed
                    active_order = check_if_actual_candle_close(ss[SYMBOL], TIMEFRAME, SMA_PERIOD,pos_open)
                    # checking if order is still active
                    #nemazat
                    active_order = check_if_active_order(ss[SYMBOL],active_order)

                #order is closed and wait till nwe candle open
                act_open = bars_df.iloc[0].open
                while act_open == open_longCandle:
                    act_open = bars_df.iloc[0].open
                    print("waiting for new candle\n")
                    time.sleep(1)

                

            """
            elif direction == 'sell':
                # if we have a SELL signal, close all short positions
                for pos in mt5.positions_get():
                    if pos.type == 0:  # pos.type == 0 represent a buy order
                        close_order(pos.ticket)
            

                # if there are no open positions, open a new short position
            if not mt5.positions_total():
                    market_order(SYMBOL, VOLUME, direction)
            """
            print('time: ', datetime.now())
            print('exposure: ', exposure)
            print('sma: ', sma)
            print('signal: ', signal1)
            print('last_close: ', last_close)
            print('last_close2: ', last_close2)
            print('last_close3: ', last_close3)
            print('-------\n')
            """
            # display the last EURUSD tick
            lasttick=mt5.symbol_info_tick("EURUSD")
            print(lasttick)
            # display tick field values in the form of a list
            print("Show symbol_info_tick(\"EURUSD\")._asdict():")
            symbol_info_tick_dict = mt5.symbol_info_tick("EURUSD")._asdict()
            for prop in symbol_info_tick_dict:
                print("  {}={}".format(prop, symbol_info_tick_dict[prop]))
            """
            # update every 1 second
            time.sleep(1)
