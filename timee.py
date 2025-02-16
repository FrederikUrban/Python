import MetaTrader5 as mt5 
import sys
from time import gmtime, strftime
from datetime import datetime
import pandas as pd  
import time

# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
else:
    print("initialize() success")

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

SYMBO = ["AUDNZD","AUDUSD","CADCHF","CADJPY","CHFJPY","EURAUD","EURCAD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD","EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD","NZDCAD","AUDCHF","AUDJPY","NZDUSD","USDCAD","USDCHF","USDJPY","AUDCAD"]

global act_price
act_price = [0.0] * len(SYMBO)



def funct():
    
    for S in range(len(SYMBO)):
        
        SYMBOL = SYMBO[S]
        bars = mt5.copy_rates_from_pos(SYMBOL, 30, 0, 8)
        bars_df = pd.DataFrame(bars)     

        act_price[S] = truncate(bars_df.iloc[-1].open,5)

    print(act_price,"\n")


time.sleep(1)

funct()
print("***",act_price,"\n")
print(len(act_price))
print(len(SYMBO))
for i in range(len(SYMBO)):
    print(SYMBO[i],"=",act_price[i])