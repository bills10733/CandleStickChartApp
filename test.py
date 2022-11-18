import pandas as pd
from cnbcfinance.cnbc import Cnbc
import datetime



#st.header('EWS Daily Signal - SPX')

#----------- Fetch data -------------

def get_current_quote(cnbc):

    quote = cnbc.get_quote()
    quote_datetime = int(quote[0]['last_time_msec'])
    quote_close = float(quote[0]['last'])
    quote_open = float(quote[0]['open'])
    quote_high = float(quote[0]['high'])
    quote_low = float(quote[0]['low'])
    quote_volume = int(quote[0]['volume'])
    lst=[{"datetime":quote_datetime,"close":quote_close,"open":quote_open,"high":quote_high,"low":quote_low,"volume":quote_volume}]
    quote_df = pd.DataFrame(lst)    
    return quote_df

#----------- Fetch data -------------

def get_current_quote_no_volume(cnbc):

    quote = cnbc.get_quote()
    quote_datetime = int(quote[0]['last_time_msec'])
    quote_close = float(quote[0]['last'])
    quote_open = float(quote[0]['open'])
    quote_high = float(quote[0]['high'])
    quote_low = float(quote[0]['low'])
    lst=[{"datetime":quote_datetime,"close":quote_close,"open":quote_open,"high":quote_high,"low":quote_low}]
    quote_df = pd.DataFrame(lst)    
    return quote_df

#-------------  Fetch full history, including adding in current day ------------------

def get_full_history(symbol):

    cnbc = Cnbc(symbol)
    df = cnbc.get_history_df(interval='1d')

    if symbol == '.VIX':
        cur_quote = get_current_quote_no_volume(cnbc)
    else:
        cur_quote = get_current_quote(cnbc)

    df.reset_index(inplace=True) #get rid of date time index - temporarily
    df=pd.concat([df,cur_quote],ignore_index=True) #add row with current quote
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms') #convert unix code to datetime
    df.set_index('datetime') # make datetime the index
    df['datetime'] = pd.to_datetime(df['datetime']).dt.date  #drop the time, just have the date

    if symbol == '.VIX':
        df.drop(['volume','open','high','low'], axis=1, inplace=True)

    return df

#-------------  Main Code ---------------

df_ES = get_full_history('@SP.1')

print(df_ES)

df_VIX = get_full_history('.VIX')
print(df_VIX)