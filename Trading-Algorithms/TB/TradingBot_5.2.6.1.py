import pandas as pd
import MetaTrader5 as mt5
import random
from datetime import datetime, timedelta

Login = 1056241391
Password = "U$=pP?U9xhsn5L"
Server = "FTMO-Demo"
def login():
    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()
    
    # connect to the trade account specifying a password and a server
    authorized=mt5.login(Login, password=Password,server = Server)
    if authorized:
        account_info=mt5.account_info()
        if account_info!=None:
            # convert the dictionary into DataFrame and print
            account_info_dict = mt5.account_info()._asdict()
            df=pd.DataFrame(list(account_info_dict.items()),columns=['property','value'])
            print("account_info() as dataframe:")
            print(df)

    else:
        print("failed to connect to trade account 1051822677 with password=****, error code =",mt5.last_error())

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
    return {'SL':SL,'minLevel':minLevel}

def NewPos():
    """ADDING NEW POSITIONS"""

    # Get all tickets for the symbol
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        print("No orders on {}, error code={}".format(symbol,mt5.last_error()))
    else:
        for position in positions:
            if str(position.ticket) in OpenPositions:
                continue
            else:
                # Add the position to the dictionary
                OpenPositions[str(position.ticket)] = getSL(position.price_open,position.symbol)
                print('New Position Added {} with ticket {} Camarila Levels{}'.format(OpenPositions[str(position.ticket)],position.ticket,Camarilla[position.symbol]))

def PP():
    """GET PIVOT POINTS"""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 1, 9)
    rates_frame = pd.DataFrame(rates)
    # convert time in seconds into the datetime format
    rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
    print(rates_frame['time'])
    
    if symbol == 'EURUSD':

        dicts['dlows_EURUSD']['time'].append(rates_frame['time'][1])
        dicts['dlows_EURUSD']['time'].append(rates_frame['time'][4])
        dicts['dhighs_EURUSD']['time'].append(rates_frame['time'][4])
        dicts['dhighs_EURUSD']['time'].append(rates_frame['time'][4])

        
        dicts['dlows_EURUSD']['time'].append(rates_frame['time'][4])
        dicts['dlows_EURUSD']['time'].append(rates_frame['time'][4])
        dicts['dlows_EURUSD']['time'].append(rates_frame['time'][4])

    # Calculate Highs L4 R4
    if rates_frame['high'][4] == max(rates_frame['high']):

        # Add to dictionary price and time 
        dicts['dhighs_'+symbol]['price'].append(rates_frame['high'][4])
        dicts['dhighs_'+symbol]['time'].append(rates_frame['time'][4])

        print('Found PP High ',dicts['dhighs_'+symbol], 'for symbol',symbol)

    # Calculate Lows L4 R4
    if rates_frame['low'][4] == min(rates_frame['low']):

        # Add to dictionary price and time 
        dicts['dlows_'+symbol]['price'].append(rates_frame['low'][4])
        dicts['dlows_'+symbol]['time'].append(rates_frame['time'][4])

        print('Found PP Low ',dicts['dlows_'+symbol], 'for symbol',symbol)


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
        
def StopLoss():
    # Get positions for symbol
    positions = mt5.positions_get(symbol=symbol)
    
    if positions is None:
        print("No orders on {}, error code={}".format(symbol,mt5.last_error()))

    else:
        for position in positions:
            if symbol == 'EURUSD':    
                print('MinLevel',OpenPositions[str(position.ticket)]['minLevel'])
                OpenPositions[str(161745764)]['minLevel'] = 1.08
                print('MinLevel',OpenPositions[str(position.ticket)]['minLevel'])
                # Check if the actual price is at the min level && PP lows size >= 3

            if OpenPositions[str(position.ticket)]['minLevel'] > position.price_current and len(dicts['dlows_'+symbol]['price']) >= 3:
                # Set SL for the ticket
                time = dicts['dlows_'+symbol]['time'][-3]

                # Delete price from the list which are older than price[-3] time 
                i = 0
                # Iterate backwards to avoid skipping elements
                while i < len(dicts['dlows_'+symbol]['time']):
                    print('i ',i,' len ',len(dicts['dlows_'+symbol]['time']))
                    print(dicts['dlows_'+symbol]['time'][i],' type',type(dicts['dlows_'+symbol]['time'][i]),' time',time,' type',type(time))  

                    if dicts['dlows_'+symbol]['time'][i] < time:
                        del dicts['dlows_'+symbol]['time'][i]
                        del dicts['dlows_'+symbol]['price'][i]
                        print('Deleted',i)
                    else:
                        i = i + 1
                i = 0
                # Delete price from the dhighs which are older than price[-3] time 
                while i < len(dicts['dhighs_'+symbol]['time']):
                    if dicts['dhighs_'+symbol]['time'][i] < time:
                        del dicts['dhighs_'+symbol]['time'][i]
                        del dicts['dhighs_'+symbol]['price'][i]
                        print('Deleted',i)
                    else:  
                        i = i + 1


                newSL = dicts['dhighs_'+symbol]['price'][-3]
                print('Seting SL ',newSL,' for ticket ',position.ticket)
                
                # If new SL is lower than the current SL
                if newSL < OpenPositions[str(position.ticket)]['SL']:
                    # Modify the SL for the ticket
                    result = modify_sl(position.ticket,symbol,newSL)
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        print("{} SL or TP faild to modify for ticket {} {}, retcode={}, SL {}, ".format(datetime.now().strftime("%H:%M:%S"),position.ticket,symbol,result.retcode,newSL))
                    else:
                        print('{} New trade added with Ticket {} {} and SL {}'.format(datetime.now().strftime("%H:%M:%S"),position.ticket,symbol,newSL))


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

login()

# major and minor symbol codes
SYMBOLS = ['AUDCAD','AUDCHF','AUDJPY','AUDNZD','AUDUSD','CADCHF','CADJPY','CHFJPY','EURAUD','EURCAD','EURCHF','EURGBP','EURJPY','EURNZD','EURUSD','GBPAUD','GBPCAD','GBPCHF','GBPJPY','GBPNZD','GBPUSD','NZDCAD','NZDCHF','NZDJPY','NZDUSD','USDCAD','USDCHF','USDJPY']
Camarilla = {}
OpenPositions = {}


# Dictionary to hold the dynamically named dictionaries
dicts = {}
createDict()
createDictHigh()

print(dicts['dlows_AUDCAD'])

for symbol in SYMBOLS:
    camarillaLevels()

while True:
    for symbol in SYMBOLS:
        # Get all tickets for the symbol and assign SL and minLevel
        NewPos()

        # Getting PP
        PP()
        if symbol == 'EURUSD':
            
            dicts['dlows_EURUSD']['price'].append(1.08)
            dicts['dlows_EURUSD']['price'].append(1.09)
            dicts['dlows_EURUSD']['price'].append(1.10)
            dicts['dlows_EURUSD']['price'].append(1.11)
            #append time to the list
            


            dicts['dhighs_EURUSD']['price'].append(1.12)
            dicts['dhighs_EURUSD']['price'].append(1.13)
            dicts['dhighs_EURUSD']['price'].append(1.14)
            dicts['dhighs_EURUSD']['price'].append(1.15)


            print('aaaaaaaaaaaa',dicts['dlows_EURUSD']['time'])

        StopLoss()

        # Check if the price is below the min level
        # elif OpenPositions[str(positions.ticket)]['minLevel'] > symbol.price_currrent and len(dicts['dlows_'+symbol]) >= 3:
        #     print('Price at min level for ticket',positions.ticket)


    # DELETE
    break

    # Load Camarila levels at 23:00 
    if datetime.now().minute == 0 and datetime.now().hour == 23:
        for symbol in SYMBOLS:
            camarillaLevels()
        print(Camarilla)




           

