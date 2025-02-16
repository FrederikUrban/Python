import MetaTrader5 as mt5
import pandas as pd
import sys
import pytz
from datetime import datetime
from time import gmtime, strftime
import time

def market_order():
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL[S],
        "volume": VOLUME,
        "type": order[S],
        "deviation": DEVIATION,
        "magic": 100,
        "comment": "Market order",
        "type_time": mt5.ORDER_TIME_SPECIFIED_DAY,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "sl": SL[S],
        "tp": TP[S]
    }

    # send a trading request
    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        ticket[S] = result.order
        print("Market order sent, ", "ticket =", result.order, "Time -> {}".format(datetime_kyjev.strftime("%H:%M:%S")))
        buy_price[S] = truncate(bars_df.iloc[-1].open,5)

        appObject = [ticket[S],diff[S],SL[S],buy_price[S],order[S],TP[S]]
        tData.append(appObject)

        print("Appended to tData: {} Time -> {}".format(appObject,datetime_kyjev.strftime("%H:%M:%S")))



    elif result.retcode == mt5.TRADE_RETCODE_MARKET_CLOSED:
        print("MARKET CLOSED")
        time.sleep(3600)

    elif result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS:
        print("Invalid SL on {} Time -> {}".format(SYMBOL,datetime_kyjev.strftime("%H:%M:%S")))

    else:
        print("ORDER FAILED retcode={} Time -> {}".format(result.retcode,datetime_kyjev.strftime("%H:%M:%S")))

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def get_sma_close(lenght,TIMEFRAME):
    bars = mt5.copy_rates_from_pos(SYMBOL[S], TIMEFRAME, 0, lenght)
    bars_df = pd.DataFrame(bars)
    SMA = bars_df.open.mean()
    return truncate(SMA,5)

def initialize():

    login = 300507255
    password = 'wdactn6vt5'
    server = 'TradersGlobalGroup-Demo'
    
    # get current date and time
    if not mt5.initialize("C:/Program Files/Traders Global Group MetaTrader 5 - Copy/terminal64.exe"):
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    else:
        print("initialize() success")
        tz_kyjev = pytz.timezone('Europe/Kiev')
        datetime_kyjev = datetime.now(tz_kyjev)
        print("Time: ",datetime_kyjev.strftime("%H:%M:%S"))

    mt5.login(login, password, server)

    acc_info = mt5.account_info()
    if acc_info is None:
        print("Failed to get account info")

    login_number = acc_info.login
    print("Login number: ", login_number)
        # establish connection to the MetaTrader 5 terminal

def printEverything():
    print("SYMBOL: ",SYMBOL[S])
    print("TIMEFRAME: ",TIMEFRAME)
    print("datetime_kyjev: ",datetime_kyjev.strftime("%H:%M:%S"))
    print("last_low: ",truncate(bars_df.iloc[-2].low,5))
    print("last_high: ",truncate(bars_df.iloc[-2].high,5))
    print("diff: ",diff[S])
    print("last_open: ",truncate(bars_df.iloc[-2].open,5))
    print("last_close: ",truncate(bars_df.iloc[-2].close,5))
    print("actual_open: ",truncate(bars_df.iloc[-1].open,5))

def findDiff():

    current_datetime = datetime.now()
    hour = current_datetime.hour
    minute = current_datetime.minute
    second = current_datetime.second
    #Ukazuje aktualny cas
    #Chcem sviecku medzi 9 a 10 hodinou v TradeView
    if hour == 10 and minute == 00 and second >= 10:
        last_low = truncate(bars_df.iloc[-2].low,5)
        last_high = truncate(bars_df.iloc[-2].high,5)
        last1_low = truncate(bars_df.iloc[-3].low,5)
        last1_high = truncate(bars_df.iloc[-3].high,5)


        #find min
        if last1_low < last_low:
            last_low = last1_low
        #find max  
        if last1_high > last_high:
            last_high = last1_high 

        if last_low == last_high:
            print("last_low == last_high on Symbol {}, Low {}, High{}, Time -> {}".format(SYMBOL[S],last_low,last_high,datetime_kyjev.strftime("%H:%M:%S")))
            return None
        
        #find difference between last_low and last_high
        diff[S] = truncate(last_high - last_low,5) if last_high > last_low else truncate(last_low - last_high,5)
        
        print("Diff on Symbol {}, Diff {}, Time -> {}".format(SYMBOL[S],diff[S],datetime_kyjev.strftime("%H:%M:%S")))
    else:
        return None

def longOrShort():
    last_open1 = truncate(bars_df.iloc[-3].open,5)
    last_close = truncate(bars_df.iloc[-2].close,5)
    
    if last_open1 == last_close:
        print("last_open == last_close on Symbol {}, Open {}, Close{}, Time -> {}".format(SYMBOL[S],last_open1,last_close,datetime_kyjev.strftime("%H:%M:%S")))
        return None

    #False = short True = long
    if last_open1 < last_close:
        print("CandleLong")
    else:
        print("CandleShort")    
    
    return True if last_open1 < last_close else False

def isGoingUp(LENGHT,TIMEFRAME):
    """SMA je klesajuca alebo stupajuca"""
    bars = mt5.copy_rates_from_pos(SYMBOL[S], TIMEFRAME, 1, LENGHT)
    bars_df = pd.DataFrame(bars)
    SMA = truncate(bars_df.close.mean(),5)

    bars = mt5.copy_rates_from_pos(SYMBOL[S], TIMEFRAME, 8, LENGHT)
    bars_df = pd.DataFrame(bars) 

    SMAm1 = truncate(bars_df.close.mean(),5)

    #True = Long False = Short
    if SMA > SMAm1 + 9*one_point:
        return True
    if SMA + 9*one_point < SMAm1:
        return False
    
    if SMA > SMAm1:
         print("BUYYY")
    elif SMA < SMAm1:
        print("SELL")

    print("SMA is not going up or down on Symbol {}, SMA {}, SMAm1{}, Time -> {}".format(SYMBOL[S],SMA,SMAm1,datetime_kyjev.strftime("%H:%M:%S")))
    return None
    
def checkSMAs():
    """ Long or Short SMA50 > or < SMA200 """
    SMA50 = get_sma_close(50,15)
    SMA200 = get_sma_close(200,15)

    if SMA50 > SMA200:
        print("long")
        return True
    elif SMA50 < SMA200:
        print("short")
        return False
    else:
        return None

def checkSL(buy_price,diff,SL,order,ticket,i,TP):
    #Check SL
   # if order is not None:

        #Long  
        if order == 0:
            actual_price = mt5.symbol_info_tick(SYMBOL[S]).bid            
            #change SL to 75% of diff
            if actual_price > actual_price + diff*0.80:
                stopLoss = truncate(actual_price + diff*0.75,5)
                if stopLoss > SL:
                    SL = stopLoss
                    print("New SL on Symbol {}, SL {}, Time -> {}".format(SYMBOL[S],SL,datetime_kyjev.strftime("%H:%M:%S")))
                    del tData[i]
                    appObject = [ticket,diff,SL,buy_price,order,TP]
                    tData.append(appObject)
                    print("Appeended tData in checkSL ",appObject)
                    modify_sl(ticket,SYMBOL[S],SL,TP)
        
        #Short 
        if order == 1:
            actual_price = mt5.symbol_info_tick(SYMBOL[S]).ask
    
            #change SL to 75% of diff
            if actual_price < actual_price - diff*0.80:
                stopLoss = truncate(actual_price - diff*0.75,5)
                if stopLoss < SL:
                    SL = stopLoss
                    print("New SL on Symbol {}, SL {}, Time -> {}".format(SYMBOL[S],SL,datetime_kyjev.strftime("%H:%M:%S")))
                    del tData[i]
                    appObject = [ticket,diff,SL,buy_price,order,TP]
                    tData.append(appObject)
                    print("Appeended tData in checkSL ",appObject)
                    modify_sl(ticket,SYMBOL[S],SL,TP)

        else:
            print("Order is None on Symbol {}, Time -> {}".format(SYMBOL[S],datetime_kyjev.strftime("%H:%M:%S")))

def modify_sl(ticket,symbol,stop_loss,tp):

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "SYMBOL": symbol,
                "position": ticket,
                "sl": stop_loss,
                "tp": tp,
                "comment": "Modified Stop Loss"
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("{} \nSL or TP faild to modify, retcode={} Time-> {}".format(ticket,result.retcode,datetime_kyjev.strftime("%H:%M:%S")))
            else:
                print("{} \nSL successfully modified on symbol {} and SL {} Time -> {}".format(ticket,SYMBOL[S],stop_loss,datetime_kyjev.strftime("%H:%M:%S")))

def checkDrawDown():
        #get open positions profit
        x = 0
        positions = mt5.positions_get()
        if len(positions) > 0:
             for pos in positions:
                    x += pos.profit
        if x < maxDailyLoss:
            print("Drawdown detected")
            closeAllPos()
        
def closeAllPos():
    if len(tData) > 0:
        for i in range(len(tData)):
            if tData[i][0] != 0:
                position = mt5.postition_get(ticket=tData[i][0])
                symbol = position.symbol
                if tData[i][4] == 0:
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": SYMBOL,
                                "volume": VOLUME,
                                "type": 1,
                                "position": tData[i][0],
                                "price": mt5.symbol_info_tick(symbol).bid,
                                "deviation": 20,
                                "magic": 100,
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                else:
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": SYMBOL,
                                "volume": VOLUME,
                                "type": 0,
                                "position": tData[i][0],
                                "price": mt5.symbol_info_tick(symbol).ask,
                                "deviation": 20,
                                "magic": 100,
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            # send a trading request
                            result = mt5.order_send(request)
                            if result != None:

                                if result.retcode == mt5.TRADE_RETCODE_DONE:
                                    print("{}\nPosition successfully closed Time -> {}".format(tData[i][0],datetime_kyjev.strftime("%H:%M:%S")))
                                    return 
                    
                            else:
                                print("{}\nClosing position failed, retcode={} Time -> {}".format(tData[i][0], result.retcode,datetime_kyjev.strftime("%H:%M:%S")))
                                return

    else:
        print("No open positions on Symbol {}, Time -> {}".format(SYMBOL[S],datetime_kyjev.strftime("%H:%M:%S")))

initialize()

SYMBOL = ["AUDNZD","AUDUSD","CADCHF","CADJPY","CHFJPY","EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD","EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD","NZDCAD","AUDCHF","AUDJPY","NZDUSD","USDCAD","USDCHF","USDJPY","AUDCAD"]
TIMEFRAME = mt5.TIMEFRAME_H1
diff = [0.0] * len(SYMBOL)
OK = [False] * len(SYMBOL)
LOR = [None] * len(SYMBOL)
SMA50 = [None] * len(SYMBOL)
SMA200 = [None] * len(SYMBOL)
checkSMA = [None] * len(SYMBOL)
order = [None] * len(SYMBOL)
SL = [0.0] * len(SYMBOL)
TP = [0.0] * len(SYMBOL)
VOLUME = 0.45
DEVIATION = 40
ticket = [0] * len(SYMBOL)
buy_price = [0.0] * len(SYMBOL)
tData = list()
appObject = [0,0.0,0.0,0.0,0,0.0]
"""ticket diff SL buy_price order tp"""
maxDailyLoss = -925



for S in range(3):



    tz_kyjev = pytz.timezone('Europe/Kiev')
    datetime_kyjev = datetime.now(tz_kyjev)

    bars = mt5.copy_rates_from_pos(SYMBOL[S], TIMEFRAME, 0, 100)
    bars_df = pd.DataFrame(bars)     

    one_point = mt5.symbol_info(SYMBOL[S]).point

    diff[S] = truncate(bars_df.iloc[-2].high - bars_df.iloc[-2].low,5)

    #Long
    print("Long on Symbol {}, Diff {}, Time -> {}".format(SYMBOL[S],diff[S],datetime_kyjev.strftime("%H:%M:%S")))
    order[S] = 0
    SL[S] = truncate(bars_df.iloc[-1].open - diff[S],5)
    TP[S] = truncate(bars_df.iloc[-1].open + diff[S]*2,5)

    print("SL on Symbol {}, SL {}, TP {}, Time -> {}".format(SYMBOL[S],SL[S],TP[S],datetime_kyjev.strftime("%H:%M:%S")))
    market_order()

    # #Short
    #     print("Short on Symbol {}, Diff {}, Time -> {}".format(SYMBOL[S],diff[S],datetime_kyjev.strftime("%H:%M:%S")))
    #     order[S] = 1
    #     SL[S] = truncate(bars_df.iloc[-1].open + diff[S],5)
    #     TP[S] = truncate(bars_df.iloc[-1].open - diff[S]*2,5)
    #     print("SL on Symbol {}, SL {},TP {}, Time -> {}".format(SYMBOL[S],SL[S],TP[S],datetime_kyjev.strftime("%H:%M:%S")))

    #     market_order()

#Check open positions
for S in range(len(SYMBOL)):
    
    bars = mt5.copy_rates_from_pos(SYMBOL[S], TIMEFRAME, 0, 100)
    bars_df = pd.DataFrame(bars)     
    positions = mt5.positions_get(symbol=SYMBOL[S])
    pomTicket = [0] * len(positions)

    checkDrawDown()


    if len(positions) > 0:
        for a in range(len(positions)):
            pomTicket[a] = positions[a].ticket

        actual_open = truncate(bars_df.iloc[-1].open,5)
        #find appended ticket and update SL and diff and buy_price 
        for i in range(len(tData)):
            for j in range(len(pomTicket)):
                if tData[i][0] == pomTicket[j]:
                    print("Ticket {} is still open".format(tData[i][0]))
                    tckt = tData[i][0]
                    difference = tData[i][1]
                    stoploss = tData[i][2]
                    buying_price = tData[i][3]
                    ordr = tData[i][4]
                    takeProfit = tData[i][5]
                    checkSL(buying_price,difference,stoploss,ordr,tckt,i,takeProfit)
                                    






