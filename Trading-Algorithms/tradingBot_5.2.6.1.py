import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import sys
from datetime import datetime
from time import gmtime, strftime
import time
import pytz

def initialize(Login,Password,Server):

    login = Login
    password = Password
    server = Server
    
    # get current date and time
    if not mt5.initialize("C:/Program Files/FTMO MetaTrader 5 - Copy/terminal64.exe"):
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

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def camarillaLevels():
    # get OHLC data for all symbols from previous day

    # GET CAMARILLA LEVELS
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 1, 1)
    rates_frame = pd.DataFrame(rates)
    # convert time in seconds into the datetime format
    rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')

    H4 = (0.55*(rates_frame['high'][0] - rates_frame['low'][0])) + rates_frame['close'][0] 
    H3 = (0.275*(rates_frame['high'][0] - rates_frame['low'][0])) + rates_frame['close'][0]
    H2 = (0.1833*(rates_frame['high'][0] - rates_frame['low'][0])) + rates_frame['close'][0]
    H1 = (0.0916*(rates_frame['high'][0] - rates_frame['low'][0])) + rates_frame['close'][0]
    L1 = rates_frame['close'][0] - (0.0916*(rates_frame['high'][0] - rates_frame['low'][0]))
    L2 = rates_frame['close'][0] - (0.1833*(rates_frame['high'][0] - rates_frame['low'][0]))
    L3 = rates_frame['close'][0] - (0.275*(rates_frame['high'][0] - rates_frame['low'][0]))
    L4 = rates_frame['close'][0] - (0.55*(rates_frame['high'][0] - rates_frame['low'][0]))

    H4 = truncate(H4, 5)
    H3 = truncate(H3, 5)
    H2 = truncate(H2, 5)
    H1 = truncate(H1, 5)
    L1 = truncate(L1, 5)
    L2 = truncate(L2, 5)
    L3 = truncate(L3, 5)
    L4 = truncate(L4, 5)

    # add camarilla levels to the dictionary for all symbols    
    Camarilla[symbol] = {'H4': H4, 'H3': H3, 'H2': H2, 'H1': H1, 'L1': L1, 'L2': L2, 'L3': L3, 'L4': L4}


def getSL(openPrice,symbol):
    '''Get the stop loss for each position based on the open price and camarilla levels and get min level'''
    # opening positions

    if openPrice > Camarilla[symbol]['H4']:
        SL = Camarilla[symbol]['H4'] - Camarilla[symbol]['H3'] + Camarilla[symbol]['H4']
        minLevel = Camarilla[symbol]['H3']

    if openPrice > Camarilla[symbol]['H3'] and openPrice < Camarilla[symbol]['H4']:
        SL = Camarilla[symbol]['H4']
        minLevel = Camarilla[symbol]['H2']

    elif openPrice > Camarilla[symbol]['H2']:
        SL = Camarilla[symbol]['H4']
        minLevel = Camarilla[symbol]['H1']

    elif openPrice > Camarilla[symbol]['H1']:
        SL = Camarilla[symbol]['H3']
        minLevel = Camarilla[symbol]['L1']

    elif openPrice > Camarilla[symbol]['L1']:
        SL = Camarilla[symbol]['H2']
        minLevel = Camarilla[symbol]['L2']

    elif openPrice > Camarilla[symbol]['L2']:
        SL = Camarilla[symbol]['H1']
        minLevel = Camarilla[symbol]['L3']

    elif openPrice > Camarilla[symbol]['L3']:
        SL = Camarilla[symbol]['L1']
        minLevel = Camarilla[symbol]['L4']

    elif openPrice > Camarilla[symbol]['L4']:
        SL = Camarilla[symbol]['L2']
        minLevel = Camarilla[symbol]['L4']

    elif openPrice <= Camarilla[symbol]['L4']:
        SL = Camarilla[symbol]['L3']
        minLevel = Camarilla[symbol]['L4']
    # get the list of positions
    #OpenPositions[ticket] = {'SL':SL,'minLevel':minLevel}
    return {'SL':SL,'minLevel':minLevel,'symbol':symbol}

def NewPos():
    """ADDING NEW POSITIONS"""

    # Get all tickets for the symbol
    positions = mt5.positions_get(symbol=symbol)
    
        
    if positions is not None:
        for position in positions:
            if str(position.ticket) in OpenPositions:
                continue
            else:
                # Add the position to the dictionary
                OpenPositions[str(position.ticket)] = getSL(position.price_open,position.symbol)
                print('{} New Position Added {} with ticket {} Camarila Levels{}'.format(datetime.now().strftime("%H:%M:%S"),OpenPositions[str(position.ticket)],position.ticket,Camarilla[position.symbol]))

def PP():
    """GET PIVOT POINTS"""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 1, 9)
    rates_frame = pd.DataFrame(rates)
    # convert time in seconds into the datetime format
    rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')

    # Calculate Highs L4 R4
    if rates_frame['high'][4] == max(rates_frame['high']):

        #check for duplicates
        if max(rates_frame['high']) in dicts['dhighs_'+symbol]['price']:
            return
        # Add to dictionary price and time 
        dicts['dhighs_'+symbol]['price'].append(rates_frame['high'][4])
        dicts['dhighs_'+symbol]['time'].append(rates_frame['time'][4])

        print('{} Found PP High {} for symbol {} '.format(datetime.now().strftime("%H:%M:%S"),dicts['dhighs_'+symbol],symbol))

    # Calculate Lows L4 R4
    if rates_frame['low'][4] == min(rates_frame['low']):

        #check for duplicates
        if min(rates_frame['low']) in dicts['dlows_'+symbol]['price']:
            return
        # Add to dictionary price and time 
        dicts['dlows_'+symbol]['price'].append(rates_frame['low'][4])
        dicts['dlows_'+symbol]['time'].append(rates_frame['time'][4])

        print('{} Found PP High {} for symbol {} '.format(datetime.now().strftime("%H:%M:%S"),dicts['dlows_'+symbol],symbol))


def createDict():
    # Number of dictionaries to generate
    num_dicts = len(SYMBOLS)

    # Generating and naming dictionaries in a loop
    for i in range(num_dicts):

        rates = mt5.copy_rates_from_pos(SYMBOLS[i], mt5.TIMEFRAME_M1, 1, 9)
        rates_frame = pd.DataFrame(rates)
        # convert time in seconds into the datetime format
        rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
        # Creating a new dictionary
        new_dict = {
            'price': i,
            'time': rates_frame['time'][4] 
        }
        
        # Convert price to a list
        new_dict['price'] = [new_dict['price']]
        new_dict['time'] = [new_dict['time']]

        # Creating a dynamic name for the dictionary
        dict_name = f'dlows_{SYMBOLS[i]}'
        
        # Storing the new dictionary in the named_dictionaries with the dynamic name as the key
        dicts[dict_name] = new_dict

    # Printing the named dictionaries
    for price, time in dicts.items():
        print(f"{price}: {time}")

def createDictHigh():
    # Number of dictionaries to generate
    num_dicts = len(SYMBOLS)
    # Generating and naming dictionaries in a loop
    for i in range(num_dicts):
        
        rates = mt5.copy_rates_from_pos(SYMBOLS[i], mt5.TIMEFRAME_M1, 1, 9)
        rates_frame = pd.DataFrame(rates)
        # convert time in seconds into the datetime format
        rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
        
        # Creating a new dictionary
        new_dict = {
            'price': i,
            'time': rates_frame['time'][4] 
        }
        
        # Convert price to a list
        new_dict['price'] = [new_dict['price']]
        new_dict['time'] = [new_dict['time']]
        
        # Creating a dynamic name for the dictionary
        dict_name = f'dhighs_{SYMBOLS[i]}'
        
        # Storing the new dictionary in the named_dictionaries with the dynamic name as the key
        dicts[dict_name] = new_dict

    # Printing the named dictionaries
    for price, time in dicts.items():
        print(f"{price}: {time}")

def setFirstSL(position):
    if position.sl == 0:
        # Set SL for the ticket
        result = modify_sl(position.ticket,symbol,OpenPositions[str(position.ticket)]['SL'])
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("{} SL failed to modify for ticket {} {}, retcode={}, SL {}, ".format(datetime.now().strftime("%H:%M:%S"),position.ticket,symbol,result.retcode,OpenPositions[str(position.ticket)]['SL']))
        else:
            print('{} Seting SL {} for ticket {}'.format(datetime.now().strftime("%H:%M:%S"),OpenPositions[str(position.ticket)]['SL'],position.ticket))

def delPPlow(time):
    i = 0
    # Iterate backwards to avoid skipping elements
    while i < len(dicts['dlows_'+symbol]['time']):
        if dicts['dlows_'+symbol]['time'][i] < time:
            print('{} Deleted element in dlows at price {}, time {}, it is lower than {} '.format(datetime.now().strftime("%H:%M:%S"),dicts['dlows_'+symbol]['price'][i],dicts['dlows_'+symbol]['time'][i],time))
            del dicts['dlows_'+symbol]['time'][i]
            del dicts['dlows_'+symbol]['price'][i]
        else:
            i = i + 1
def delPPhigh(time):
    i = 0
    while i < len(dicts['dhighs_'+symbol]['time']):
        if dicts['dhighs_'+symbol]['time'][i] < time:
            print('{} Deleted element in dhighs at price {}, time {}, it is lower than {}'.format(datetime.now().strftime("%H:%M:%S"), dicts['dhighs_'+symbol]['price'][i], dicts['dhighs_'+symbol]['time'][i], time))
            del dicts['dhighs_'+symbol]['time'][i]
            del dicts['dhighs_'+symbol]['price'][i]
        else:  
            i = i + 1

def StopLoss():
    # Get positions for symbol
    positions = mt5.positions_get(symbol=symbol)
    
    if positions is None:
        print("No orders on {}, error code={}".format(symbol,mt5.last_error()))

    else:
        for position in positions:

           # Set first sl
            setFirstSL(position)
            
            # Check if the actual price is at the min level && PP lows size >= 3
            if OpenPositions[str(position.ticket)]['minLevel'] > position.price_current:
                # Set SL for the ticket
                if len(dicts['dlows_'+symbol]['time']) >= 3:
                    time = dicts['dlows_'+symbol]['time'][-3]

                    # Delete price from the list which are older than price[-3] time 
                    delPPlow(time)

                    # Delete price from the dhighs which are older than price[-3] time 
                    delPPhigh(time)

                    if len(dicts['dlows_'+symbol]['price']) >= 3:
                        newSL = max(dicts['dhighs_'+symbol]['price'][-3])
                        
                        # If new SL is lower than the current SL
                        if newSL < OpenPositions[str(position.ticket)]['SL']:
                            # Modify the SL for the ticket
                            result = modify_sl(position.ticket,symbol,newSL)
                            if result.retcode != mt5.TRADE_RETCODE_DONE:
                                print("{} SL failed to modify for ticket {} {}, retcode={}, SL {}, ".format(datetime.now().strftime("%H:%M:%S"),position.ticket,symbol,result.retcode,newSL))
                            else:
                                print('{} Seting SL {} for ticket {}'.format(datetime.now().strftime("%H:%M:%S"),newSL,position.ticket))



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

#Delete closed positions
def deleteClosed(): 

    ticketList = []
    # Get all ticket for the symbol
    for key, value in OpenPositions.items():
        # if value symbol is equal to symbol then add ticket to the list
        if value['symbol'] == symbol:
            ticketList.append(key)
    # Get all positions for the symbol
    positions = mt5.positions_get(symbol=symbol)
    # Iterate through the positions
    for position in positions:
        # If the position is not in the ticket list then delete it
        if str(position.ticket) not in ticketList:
            print('{} Deleting position {}'.format(datetime.now().strftime("%H:%M:%S"),position.ticket))
            del OpenPositions[key]
        
Login = 1056242534
Password = "9VzZutUq@*P"
Server = "FTMO-Demo"

# major and minor symbol codes
SYMBOLS = ['AUDCAD','AUDCHF','AUDJPY','AUDNZD','AUDUSD','CADCHF','CADJPY','CHFJPY','EURAUD','EURCAD','EURCHF','EURGBP','EURJPY','EURNZD','EURUSD','GBPAUD','GBPCAD','GBPCHF','GBPJPY','GBPNZD','GBPUSD','NZDCAD','NZDCHF','NZDJPY','NZDUSD','USDCAD','USDCHF','USDJPY']
Camarilla = {}
OpenPositions = {}
# Dictionary to hold the dynamically named dictionaries
dicts = {}

initialize(Login,Password,Server)
createDict()
createDictHigh()

for symbol in SYMBOLS:
    camarillaLevels()
    print('{} Camarilla Levels {} for symbol {}'.format(datetime.now().strftime("%H:%M:%S"),Camarilla[symbol],symbol))

while True:
    for symbol in SYMBOLS:

        path = 'C:\TradingBot\Log5-2-6-1\Log_'+symbol+str(strftime("%m_%Y", gmtime()))+'.txt'
        sys.stdout = open(path, 'a')
        # Get all tickets for the symbol and assign SL and minLevel
        NewPos()

        # Getting PP
        PP()

        StopLoss()

        deleteClosed()

    # Load Camarila levels at 23:00 
    if datetime.now().minute == 0 and datetime.now().hour == 23:
        for symbol in SYMBOLS:
            camarillaLevels()
            print('{} Camarilla Levels {} for symbol {}'.format(datetime.now().strftime("%H:%M:%S"),Camarilla[symbol],symbol))
            # Wait a minute
        time.sleep(60)
