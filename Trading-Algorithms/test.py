import MetaTrader5 as mt5
import pandas as pd
import sys
import pytz
from datetime import datetime
from time import gmtime, strftime
import time

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


def initialize(Login,Password,Server):

    login = Login
    password = Password
    server = Server
    
    # get current date and time
    if not mt5.initialize("C:/Program Files/FTMO MetaTrader 5/terminal64.exe"):
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

def modify_sl(ticket,symbol,stop_loss):

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "SYMBOL": symbol,
                "position": ticket,
                "sl": stop_loss,
                "comment": "Modified Stop Loss"
            }

            result = mt5.order_send(request)
            return result

def GetNewTrades():
    path = 'C:\TradingBot\Log5-2-2\Log_'+str(strftime("%m_%Y", gmtime()))+'.txt'
    sys.stdout = open(path, 'a')
    
    positions = mt5.positions_get()

    for a in range(len(positions)):
        #If position have SL, it is already in List
        if positions[a].sl != 0.0:
            continue
        #If position is long
        if positions[a].type == 0:
            continue
        
        point = mt5.symbol_info(positions[a].symbol).point
        #Add position to List
        newPos = [positions[a].ticket,positions[a].symbol,positions[a].volume,positions[a].price_open,positions[a].price_open + SL[0]*point,None]
        newPos1 = [None,positions[a].symbol,positions[a].volume,positions[a].price_open - 20*point,positions[a].price_open + SL[1]*point,None]
        newPos2 = [None,positions[a].symbol,positions[a].volume,positions[a].price_open - 40*point,positions[a].price_open + SL[2]*point,None]
        newPos3 = [None,positions[a].symbol,positions[a].volume,positions[a].price_open - 60*point,positions[a].price_open + SL[3]*point,None]
        List.append([newPos,newPos1,newPos2,newPos3])

        #Set SL to first position
        result = modify_sl(positions[a].ticket,positions[a].symbol,newPos[4])

        if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("{} SL or TP faild to modify for ticket {} {}, retcode={}, SL {}, ".format(datetime.now().strftime("%H:%M:%S"),result.deal,positions[a].symbol,result.retcode,newPos[4]))
        else:
                print('{} New trade added with Ticket {} {} and SL {}'.format(datetime.now().strftime("%H:%M:%S"),positions[a].ticket,positions[a].symbol,newPos[4]))

        

def market_order(symbol,volume,sl):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": 1,
        "magic": 100,
        "comment": "Market order",
        "type_time": mt5.ORDER_TIME_SPECIFIED_DAY,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "sl": sl
    }


    # send a trading request
    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:

        print("{} Market order sent on ticket {} for {} {} with SL {}".format(datetime.now().strftime("%H:%M:%S"),result.order,symbol,volume,sl))


    elif result.retcode == mt5.TRADE_RETCODE_MARKET_CLOSED:
        print("{} MARKET CLOSED {}".format(datetime.now().strftime("%H:%M:%S"),symbol))
        time.sleep(3600)

    elif result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS:
        print("{} Invalid SL on Symbol {}".format(datetime.now().strftime("%H:%M:%S"),symbol))

    else:
        print("{} ORDER FAILED retcode={} {}".format(datetime.now().strftime("%H:%M:%S"),result.retcode,symbol))

    return result

def OpenTrades():
     for S in range(len(SYMBOL)):
        symPrice = mt5.symbol_info_tick(SYMBOL[S])
        #Iterate over List and check open price of every position with None ticket
        for i in range(len(List)):
            #Check symbol 
            if List[i][0][1] != SYMBOL[S]:
                continue
            #If position is already opened, skip it
            for x in range(4):
                if List[i][x][0] != None:
                    continue
                #If position is not opened, check if open price is reached
                if List[i][x][3] >= symPrice:
                    #Open position
                    result = market_order(SYMBOL[S],List[i][x][2],List[i][x][4])
                    #Modify List
                    ticket = result.order
                    List[i][x][0] = ticket

                    #Modify previous positions sl
                    for z in range(x-1,-1,-1):
                        result = modify_sl(List[i][z][0],SYMBOL[S],List[i][x][4])

                        if result.retcode != mt5.TRADE_RETCODE_DONE:
                                print("{} SL or TP faild to modify for ticket {} {}, retcode={}, SL {}, ".format(datetime.now().strftime("%H:%M:%S"),result.deal,SYMBOL[S],result.retcode,List[i][x][4]))
                        else:
                                print('{} New trade added with Ticket {} {} and SL {}'.format(datetime.now().strftime("%H:%M:%S"),result.deal,SYMBOL[S],List[i][x][4]))

def ModifySL6():   
    #Iterate over List and check open price of first position
    for i in range(len(List)):

        symPrice = mt5.symbol_info_tick(List[i][0][1]).ask
        point = mt5.symbol_info(List[i][0][1]).point
        for x in range(4):
            symInfo = mt5.symbol_info(List[i][x][0])

            if symInfo == None:
                break

            #Check if exist all 4 positions
            if List[i][3][0] == None:
                break
            
            #Check if open price - 8 pips is reached
            if List[i][0][3] - 80*point < symPrice:
                break
            
            #New SL has to be lower than previous SL
            if symInfo[0].sl < List[i][0][3] - 60*point:
                break

            result = modify_sl(List[i][x][0],List[i][x][1],List[i][0][3] - 60 * point)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print("{} SL or TP faild to modify for ticket {} {}, retcode={}, SL {}, ".format(datetime.now().strftime("%H:%M:%S"),result.deal,List[i][x][1],result.retcode,List[i][0][3] - 60 * point))
            else:
                    print('{} New trade added with Ticket {} {} and SL {}'.format(datetime.now().strftime("%H:%M:%S"),result.deal,List[i][x][1],List[i][0][3] - 60 * point))

def ModifySLhigh():
    for S in range(len(SYMBOL)):
        for i in range(len(List)):
            if List[i][0][1] != SYMBOL[S]:
                continue

            #If last position is not opened, skip
            if List[i][3][0] == None:
                continue

            symPrice = mt5.symbol_info_tick(SYMBOL[S]).ask
            point = mt5.symbol_info(SYMBOL[S]).point
            bars = mt5.copy_rates_from_pos(SYMBOL[S], mt5.TIMEFRAME_M5, 0, 10)
            bars_df = pd.DataFrame(bars)
            lastHigh = truncate(bars_df.iloc[-2].high,5)

            #Iterate over all 4 positions and check if SL should be modified
            for x in range(4):
                posInfo = mt5.positions_get(ticket=List[i][x][0])
                firstPosInfo = mt5.positions_get(ticket=List[i][0][0])

                if posInfo==None:
                    print("{} No positions on {} {}, error code={}".format(datetime.now().strftime("%H:%M:%S"),List[i][x][0],SYMBOL[S],mt5.last_error()))
                if firstPosInfo==None:
                    print("{} No positions on firstPosInfo {} {}, error code={}".format(datetime.now().strftime("%H:%M:%S"),List[i][0][0],SYMBOL[S],mt5.last_error()))

                if len(posInfo) == 0:
                    break

                if len(firstPosInfo) == 0:
                    break

                #if last position is not opened, break
                if List[i][3][0] == None:
                    break

                #Has to be bearish candle
                if bars_df.iloc[-2].close > bars_df.iloc[-2].open:
                    break

                #Body has to be bigger than C - L
                if bars_df.iloc[-2].close - bars_df.iloc[-2].low > bars_df.iloc[-2].open - bars_df.iloc[-2].close:
                    break
                
                #ask has to be lower than lastHigh - 10 pips
                if symPrice > lastHigh - 10*point:
                    break
                
                #ask has to be lower than OP first position - 80 pips
                if symPrice > firstPosInfo[0].price_open - 80*point:
                    break

                #last high has to be lower than OP first position - 60 pips
                if lastHigh > firstPosInfo[0].price_open - 60*point:
                    break

                #last high has to be lower than SL - 10 pips
                if lastHigh > posInfo[0].sl - 10*point:
                    break
                
                #Check if is created lower
                if bars_df.iloc[-3].low < bars_df.iloc[-2].low:
                    break
                
                #First modification
                if List[i][x][5] == None:
                    List[i][x][5] = bars_df.iloc[-2].low
                    
                #last low has to be lower than previous low
                if bars_df.iloc[-2].low > List[i][x][5]:
                    break
                
                #Set new low
                List[i][x][5] = bars_df.iloc[-2].low

                result = modify_sl(List[i][x][0],SYMBOL[S],lastHigh)

                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print("{} SL or TP faild to modify for ticket {} {}, retcode={}, SL {}, ".format(datetime.now().strftime("%H:%M:%S"),List[i][x][0],SYMBOL[S],result.retcode,lastHigh))
                else:
                    print('{} SL modified {} {} and SL: {}, current ask price: {}, pips from first OP: {}'.format(datetime.now().strftime("%H:%M:%S"),List[i][x][0],SYMBOL[S],lastHigh,symPrice,(firstPosInfo[0].price_open - symPrice) * 10 ))
                
def removePositions():
    i = 0
    while i < (len(List)):
        ticket = List[i][0][0]
        result = mt5.positions_get(ticket=ticket)
        if result == None:
            print("{} Removing position {}".format(datetime.now().strftime("%H:%M:%S"),List[i]))
            del List[i]
            print("Remaining positions in list: ",List)
            
        else:
            i += 1
Login = 62056498
Password = 'Epox2aijw_'
Server = 'PepperstoneUK-Demo'
SYMBOL = ['AUDCAD','AUDCHF','AUDJPY','AUDNZD','AUDUSD','CADCHF','CADJPY','CHFJPY','EURAUD','EURCAD','EURCHF','EURGBP','EURJPY','EURNZD','EURUSD','GBPAUD','GBPCAD','GBPCHF','GBPJPY','GBPNZD','GBPUSD','NZDCAD','NZDCHF','NZDJPY','NZDUSD','USDCAD','USDCHF','USDJPY']
List = []
SL = [900,450,225,112.5] #Points
initialize(Login,Password,Server)

# display the last GBPUSD tick
lasttick=mt5.symbol_info_tick("GBPUSD")
print(lasttick)
# display tick field values in the form of a list
print("Show symbol_info_tick(\"GBPUSD\")._asdict():")
symbol_info_tick_dict = mt5.symbol_info_tick("GBPUSD")._asdict()
for prop in symbol_info_tick_dict:
    print("  {}={}".format(prop, symbol_info_tick_dict[prop]))
 
print('bid',mt5.symbol_info_tick("GBPUSD").bid)


while True:

    GetNewTrades()

    OpenTrades()

    ModifySLhigh()

    removePositions()

    time.sleep(1)