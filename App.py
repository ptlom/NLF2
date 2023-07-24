# Front end file for portfolio.

import streamlit as st
import quantportfolio as qp
from datetime import datetime as dt, timedelta
from sqlaccess import get_connection

st.set_page_config(
    page_title = "Homepage",
    page_icon = "club_logo.jpg"
)

# access Portfolio methods 
myp = qp.Portfolio(None, None)
# create new connection for front-end
db = get_connection()
newcursor = db.cursor()

st.markdown("# Nittany Lion Fund")

option = st.selectbox(
    'Select your sector',
    ('NLF', 'COMM', 'CD', 'CS', 'E', 'FIN', 'H', 'IND', 'IT', 'MAT', 'RE', 'U'))



st.write("## Holdings")
st.write("Note: prices are expressed in cents for more precise arithmetic")
holdings = myp.sql_to_pd_dataframe("holdings", db)
st.dataframe(holdings)

st.write("## Latest Trades")
trades = myp.sql_to_pd_dataframe("trades", db)
st.dataframe(trades.tail(5))

st.write("## Breakdown")
col1, col2 = st.columns(2)
with col1:
    st.write("### Stocks")
    st.write(myp.draw_stocks_diversity(newcursor))
with col2:
    st.write("### Sectors")
    st.write(myp.draw_sectors_diversity(newcursor))

today_date = dt.now()
start = st.sidebar.date_input("Start date", today_date - timedelta(days=3*365))
end = st.sidebar.date_input("End date", today_date)

stocks_in_holding = myp.get_stocks_in_holding(newcursor)

if len(stocks_in_holding) > 0:
    close_holding_table = myp.get_close_price(start,end, newcursor)
    st.write(f"### Holdings for {', '.join(stocks_in_holding)}")
    st.write("Visit the sidebar to choose a different date")
    st.write(close_holding_table)
    st.write("### Holdings Returns")
    st.line_chart(close_holding_table)
else:
    st.write("No stock in holding")
