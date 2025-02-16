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
                "symbol": symbol,
                "position": ticket,
                "sl": stop_loss,
                "comment": "Modified Stop Loss"
            }

            result = mt5.order_send(request)
            return result


Login = 1520336241
Password = 'sIq!se5X$$m6'
Server = 'FTMO-Demo2'
SYMBOL = ['AUDCAD','AUDCHF','AUDJPY','AUDNZD','AUDUSD','CADCHF','CADJPY','CHFJPY','EURAUD','EURCAD','EURCHF','EURGBP','EURJPY','EURNZD','EURUSD','GBPAUD','GBPCAD','GBPCHF','GBPJPY','GBPNZD','GBPUSD','NZDCAD','NZDCHF','NZDJPY','NZDUSD','USDCAD','USDCHF','USDJPY']
List = []
SL = [900,450,225,112.5] #Points
initialize(Login,Password,Server)


def market_order(symbol,volume,sl):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_SELL,
        "magic": 100,
        "comment": "Market order",
        "type_time": mt5.ORDER_TIME_SPECIFIED_DAY,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "sl": sl,
    }



    # send a trading request
    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:

        print("{} Market order sent on ticket {} for {} {} with SL {}".format(datetime.now().strftime("%H:%M:%S"),result.order,symbol,volume,sl))

market_order('AUDJPY',0.01,97.500)