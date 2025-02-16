import sys

# import module
from datetime import datetime
  
# get current date and time
current_datetime = datetime.now()

month = current_datetime.month
day = current_datetime.day
year = current_datetime.year

currentTime = current_datetime.strftime("{}.{}.{}".format (day, month,year))
path = 'C:\TradingBot\Log\Log-'+str(currentTime)+'.txt'

  
# convert datetime obj to string
str_current_datetime = str(currentTime)
  
# create a file object along with extension
file_name = currentTime+".txt"



print("path",path)

sys.stdout = open(path, 'w')
print ("Hello World")

