import pandas as pd
import streamlit as st
from cnbcfinance.cnbc import Cnbc
import plotly.graph_objects as go
#from datetime import datetime
import datetime

st.sidebar.write('sidebar - not in use')

#st.header('EWS Daily Signal - SPX')

cnbc = Cnbc('SPX')
df = cnbc.get_history_df(interval='1d')

df.reset_index(inplace=True)

df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
df.set_index('datetime')

print(df)

#quote = cnbc.get_quote()
#quote[0]['last']

fig = go.Figure(data=[go.Candlestick(x=df['datetime'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])
fig.update_xaxes(type='category')
st.plotly_chart(fig, use_container_width=True)
#fig.show()