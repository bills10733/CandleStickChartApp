import pandas as pd
import streamlit as st
from cnbcfinance.cnbc import Cnbc
import plotly.graph_objects as go
import datetime

#st.header('EWS Daily Signal - SPX')

#----------- Fetch data -------------

cnbc = Cnbc('@SP.1')
df = cnbc.get_history_df(interval='1d')

df.reset_index(inplace=True)

df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
df.set_index('datetime')
df['datetime'] = pd.to_datetime(df['datetime']).dt.date

quote = cnbc.get_quote()
quote
quote_open = quote[0]['open']
quote_high = quote[0]['high']
quote_low = quote[0]['low']
quote_close = quote[0]['last']
quote_volume = quote[0]['volume']

fig = go.Figure(data=[go.Candlestick(x=df['datetime'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])
fig.update_xaxes(type='category')
st.plotly_chart(fig, use_container_width=True)
#fig.show()
