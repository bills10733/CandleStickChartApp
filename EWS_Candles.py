import pandas as pd
from cnbcfinance.cnbc import Cnbc
import datetime
from datetime import date
import pandas_datareader as pdr
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf
yf.pdr_override()

#----------- Fetch current-day quote for VIX data  -------------

def get_current_quote(cnbc):

    quote = cnbc.get_quote()
    quote_datetime = int(quote[0]['last_time_msec'])
    quote_close = float(quote[0]['last'])
    quote_open = float(quote[0]['open'])
    quote_high = float(quote[0]['high'])
    quote_low = float(quote[0]['low'])
    lst=[{"datetime":quote_datetime,"close":quote_close,"open":quote_open,"high":quote_high,"low":quote_low}]
    return pd.DataFrame(lst)

#-------------  Fetch full history of VIX futures, including adding in current day ------------------

def get_VIX_history(symbol):

    cnbc = Cnbc(symbol)
    df = cnbc.get_history_df(interval='1d')
    cur_quote = get_current_quote(cnbc)

    df.reset_index(inplace=True) #get rid of date time index - temporarily
    df=pd.concat([df,cur_quote],ignore_index=True) #add row with current quote
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms') #convert unix code to datetime
    df['datetime'] = pd.to_datetime(df['datetime']).dt.date  #drop the time, just have the date
    df.drop(['volume','open','high','low'], axis=1, inplace=True)

    return df

#-------------  Primary Block to get all VIX data and calculate IVTS ---------------

def IVTS(vix9d, vix, vix3m, vix6m):
    if vix9d < vix and vix < vix3m and vix3m < vix6m:
        ivts = 0
    else:
        ivts = 1
    return ivts

def get_IVTS():
    df_VIX = get_VIX_history('.VIX')
    df_VIX9D = get_VIX_history('.VIX9D')
    df_VIX3M = get_VIX_history('.VIX3M')
    df_VIX6M = get_VIX_history('.VIX6M')
    df_temp1 = pd.merge(df_VIX9D,df_VIX, on='datetime')
    df_temp2 = pd.merge(df_temp1,df_VIX3M, on='datetime')
    df_temp2.columns = ['datetime', 'VIX9D', 'VIX','VIX3M']
    df_All = pd.merge(df_temp2,df_VIX6M, on='datetime')
    df_All.columns = ['datetime', 'VIX9D', 'VIX', 'VIX3M','VIX6M']
    df_All.drop_duplicates(subset=['VIX9D', 'VIX', 'VIX3M','VIX6M'],inplace=True)
    df_All['IVTS'] = df_All.apply(lambda row: IVTS(row["VIX9D"],row["VIX"],row["VIX3M"],row['VIX6M']),axis=1)
    return df_All

#-----------  End of IVTS section -----------------

#-----------------------------------------------------------
#------ Section for Calculating Force Index   --------------
#-----------------------------------------------------------

# function to calculate Force Index - returns 13 day FI
def ForceIndex(data): 
    FI = pd.Series((data['Close'].diff(1) * data['Volume'])/1000000, name = 'ForceIndex')
    FI = FI.ewm(span=13, adjust=False).mean()
    data = data.join(FI)
    data.drop(['Volume','Open','High','Low','Adj Close','Close'], axis=1, inplace=True)
    data.reset_index(inplace=True) #get rid of date time index - temporarily
    data.rename(columns={'Date': 'datetime'}, inplace=True)
    return data

# function to Retrieve One-Year of ES data from Yahoo finance
def RetrieveData(symbol):
    data = pdr.get_data_yahoo(symbol, start= str(date.today()-datetime.timedelta(days = 400)), end=str(date.today())) 
    data = pd.DataFrame(data)
    return data

def FI_fires(fi_es, fi_spy):
    if fi_es < -15 and fi_spy < -141:
        FI = 2
    elif fi_es > -15 and fi_spy > -141:
        FI = 0
    else: FI=1
    return FI

# Compute the Force Index and current signal
ES_ForceIndexDF = ForceIndex(RetrieveData('ES=F'))
SPY_ForceIndexDF = ForceIndex(RetrieveData('SPY'))

FI_df = pd.merge(ES_ForceIndexDF,SPY_ForceIndexDF, on='datetime')
FI_df.columns = ['datetime', 'FI_ES', 'FI_SPY']
FI_df['FI_State'] = FI_df.apply(lambda row: FI_fires(row["FI_ES"],row["FI_SPY"]),axis=1)


#-----------------------------------------------------------
#------------- Merge IVTS and FI data   --------------------
#-----------------------------------------------------------

def EWS_Signal(ivts, fi):
    if ivts == 0 and fi == 0:
        ews = 0
    elif ivts == 1 and fi == 2:
        ews = 2
    else: ews = 1
    return ews


IVTS_df = get_IVTS()
IVTS_df['datetime'] =  pd.to_datetime(IVTS_df['datetime'])

Big_df = pd.merge(IVTS_df,FI_df, on='datetime')
Big_df['EWS_State'] = Big_df.apply(lambda row: EWS_Signal(row["IVTS"],row["FI_State"]),axis=1)


#---------------------------------------------------

fig_df = RetrieveData('ES=F')
fig_df.reset_index(inplace=True) #get rid of date time index - temporarily
fig_df.rename(columns={'Date': 'datetime'}, inplace=True)

EWS_State_df = Big_df.drop(['VIX9D','VIX','VIX3M','VIX6M','IVTS','FI_ES','FI_SPY','FI_State'], axis=1)
Final_df = pd.merge(fig_df, EWS_State_df, on='datetime')
Final_df['datetime'] = pd.to_datetime(Final_df['datetime']).dt.date
#Final_df['SMA20'] = Final_df['Close'].rolling(window=20).mean()

#---------------------------------------------------
#------------  Plotting ----------------------------
#---------------------------------------------------


fig = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.01, 
                    row_heights=[0.9,0.1])

fig.add_trace(go.Candlestick(x=Final_df['datetime'],
                             open=Final_df['Open'],
                             high=Final_df['High'],
                             low=Final_df['Low'],
                             close=Final_df['Close'], 
                             showlegend=False))


colors = ['green' if row['EWS_State'] == 0 else 'yellow' if row['EWS_State'] == 1
          else 'red' for index, row in Final_df.iterrows()]

fig.add_trace(go.Scatter(x=Final_df['datetime'], 
                     y=Final_df['EWS_State'],
                     mode='markers', 
                     marker=go.scatter.Marker(),
                     marker_color=colors,
                    ), row=2, col=1)

fig.update_xaxes(type='category')
fig.update_layout(xaxis_rangeslider_visible=False, showlegend=False,
                    paper_bgcolor='black',plot_bgcolor='black', font_color="white",
                    margin=go.layout.Margin(
                        l=20, #left margin
                        r=20, #right margin
                        b=20, #bottom margin
                        t=20)  #top margin 
                        )
fig.for_each_xaxis(lambda x: x.update(showgrid=False, zeroline = False))
fig.for_each_yaxis(lambda x: x.update(showgrid=False, zeroline = False))

fig.show()
#st.plotly_chart(fig, use_container_width=True) # this line for plot in StreamLit
#print(Final_df)