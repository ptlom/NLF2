import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib as plt
import matplotlib.pyplot as plt
import mysql.connector as mysql
import random
from pandas_datareader import data as pdr
from sqlaccess import get_connection as get_db_connection
from sqlaccess import get_connection as get_user
import webbrowser as wb
yf.pdr_override()

# Establishes connection with the database. Enter the details in sqlaccess.py.
mydb = get_db_connection()
mycursor = mydb.cursor()

'''
Portfolio methods for front-end should have mysql connection as optional parameter. If no argument is passed, the method should use 
mycursor defined above. Ex: sql_to_pd_dataframe(self, table, mydb = mydb)
'''

class Portfolio:
  def __init__(self, name, cash):
    self.name = name
    self.cash = cash
    self.AUM = None
    self.portfolio_beta = None
    
    self.profit_loss = None
    self.sharpe_ratio = None
    self.total_return = None
    self.expense_ratio = None
    self.avg_price_to_earnings = None

 
  def sql_to_pd_dataframe(self, table, mydb = mydb):
    df = pd.read_sql(f'SELECT * FROM tradedb.{table}', con = mydb)
    return df
  
  # Could access existing ids through query
  def generate_order_id(self, table):
    mycursor.execute(f'SELECT order_id FROM tradedb.{table}')
    existing_ids = list(mycursor.fetchall())
    order_id = random.randint(0, 9999999999)
    if order_id in existing_ids:
      while order_id not in existing_ids:
        order_id = random.randint(0, 9999999999)
    
    return order_id

  def usd_to_cents(self, amount):
    cents = amount * 100
    return cents

  # calculates assets under management
  def calculate_AUM(self):
    holdings_df = self.sql_to_pd_dataframe("holdings")
    holdings_df["current_price"] = holdings_df["ticker"].apply(lambda x: self.get_latest_price(x))
    holdings_df['cp_times_q'] = holdings_df.current_price * holdings_df.quantity
    self.AUM = (holdings_df['cp_times_q'].sum()) / 100
    return self.AUM

  # Ex: 
  def performance_vs_benchmark(self, start_date, end_date, benchmark):
    portfolio_returns = self.expected_annual_return(self. start_date, end_date)
    benchmark_returns = self.calculate_security_return(start_date, end_date, benchmark)
    performance_difference = portfolio_returns - benchmark_returns
    return performance_difference
    # changes datetime64 to datetime.datetime format
    #df['time'] = df['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
  
  
  def calculate_security_return(self, start_date, end_date, security):
    price_data = pd.DataFrame()
    price_data[security] = pdr.get_data_yahoo(security, start = start_date, end = end_date)['Adj Close']
    returns = (price_data / price_data.shift(1)) - 1 # daily returns
    annual_returns = returns.mean() * 252
    return annual_returns

  def positions_weight(self, ticker):
    quantity_query = f"SELECT quantity FROM holdings WHERE ticker = {ticker}"
    mycursor.execute(quantity_query)
    
    current_price = self.get_latest_price(ticker)
    self.AUM = self.calculate_AUM()
    position_weight = (quantity_query * current_price) / self.AUM

    return position_weight

  # returns expected annual returns over the given time interval
  # Ex: expected_annual_return(datetime(2000, 12, 16), datetime(2012, 12, 16))
  def expected_annual_return(self, start_date, end_date):
    tickers = {}
    mycursor.execute('SELECT ticker FROM tradedb.holdings')

    for row in mycursor:
      for field in row:
        if not (field in tickers):
          tickers[field] = 1

    weights = []
    tickers = list(tickers)
    price_data = pd.DataFrame()
    for t in tickers:
      price_data[t] = pdr.get_data_yahoo(t, start = start_date, end = end_date)['Adj Close']
      weights.append(self.positions_weight(t))
    returns = (price_data / price_data.shift(1)) - 1 # daily returns

    # array of dot products with daily returns
    # each entry in the array represents a daily return of the portfolio
    np.dot(returns, weights)
    annual_returns = returns.mean() * 252
    expected_annual_return = np.dot(annual_returns, weights)
    return expected_annual_return

  # get latest price of a stock
  def get_latest_price(self, ticker):
    try:
      return yf.Ticker(ticker).info["currentPrice"]
    except:
      print("The stock ticker is incorrect.")
      return 0.0

  # find past trades from tradedb.trades
  def find_us_stock_trade(self, ticker, id):
      stock_table = pd.read_sql("SELECT * FROM tradedb.trades WHERE ticker = %s AND order_id = %s ", con=mydb, params=[ticker,id])
      print(f"{len(stock_table)} results found !")
      # if no trades were found, return empty dataframe
      return stock_table if len(stock_table) > 0 else pd.DataFrame()
  
  def view_webpage(self):
      wb.open("https://quant-web.streamlit.app/", new=2)

  # specify the format of this method so that the SQL query works properly
  # buys/sells US stock
  def place_US_stock_order(self, ticker, price, order_type, quantity):
    total_cost = price * quantity  # convert to cents later

    if order_type == "B":
      if total_cost > self.cash:
        print("Not enough funds")
        print(f"Order Cost: ${total_cost}, Balance: ${self.cash}")
      else:
        # don't forget to store the purchase price in cents on MySQL for floating point precision
        self.cash -= total_cost
        buy_query = f"INSERT INTO tradedb.trades (order_id, user_id, order_type, ticker, price, quantity)\
                      VALUES ({self.generate_order_id('trades')}, {get_user()}, {order_type}, {ticker}, {self.usd_to_cents(total_cost)},\
                      {quantity});"
        mycursor.execute(buy_query)
        # commit changes to database
        mydb.commit()
        print(f"You purchased ${total_cost} of {ticker}")

    if order_type == "S":
        self.cash += total_cost
        sell_query = f"INSERT INTO tradedb.trades (order_id, user_id, order_type, ticker, price, quantity)\
                      VALUES ({self.generate_order_id('trades')}, {get_user()}, {order_type}, {ticker}, {self.usd_to_cents(total_cost)},\
                      {quantity});"
        mycursor.execute(sell_query)
        mydb.commit()
        print(f"You sold ${total_cost} of {ticker}")
    
    else:
      # raise an error/exception, print error for now
      print("Order type can be either 'B' (buy) or 'S' (sell)")

  #calculates the standard deviation of returns
  def sd_of_returns(self, start_date, end_date):
    tickers = {}
    mycursor.execute('SELECT ticker FROM tradedb.holdings')

    for row in mycursor:
      for field in row:
        if not (field in tickers):
          tickers[field] = 1

    weights = np.array([])
    tickers = list(tickers)
    price_data = pd.DataFrame()
    for t in tickers:
      price_data[t] = pdr.get_data_yahoo(t, start = start_date, end = end_date)['Adj Close']
      weights.append(positions_weight(t))
    returns = (price_data / price_data.shift(1)) - 1 # daily returns

    # array of dot products with daily returns
    # each entry in the array represents a daily return of the portfolio
    np.dot(returns, weights)
    returns_annual_sd = returns.std() * 252 ** 0.5
    return returns_annual_sd 
  
  def get_risk_free_rate(self): 
    risk_free_rate=yf.download('^IRX')['Adj Close'].iloc[-1]
    return risk_free_rate

  # Ex: calculate_sharpe_ratio(datetime(2000, 12, 16), datetime(2012, 12, 16))
  def calculate_sharpe_ratio(self, start_date, end_date): 
    annual_sd = self.sd_of_returns(start_date, end_date)
    expected_annual_return = self.expected_annual_return(start_date, end_date)
    rfr = self.get_risk_free_rate()
    sharpe_ratio = (expected_annual_return - rfr) / annual_sd
    return sharpe_ratio

  
  # Ex: graph_holdings_returns(datetime(2000, 12, 16), datetime(2012, 12, 16))
  def graph_holdings_returns(self, start_date, end_date):
    tickers = {}
    mycursor.execute('SELECT ticker FROM tradedb.holdings')

    for row in mycursor:
      for field in row:
        if not (field in tickers):
          tickers[field] = 1

    tickers = list(tickers)
    stock_data = pd.DataFrame()
    stock_data = pdr.get_data_yahoo(tickers, start = start_date, end = end_date)['Adj Close']
    (stock_data / stock_data.iloc[0] * 100).plot(figsize = (15,6))

  def get_stock_beta(self, ticker):
    try:
      return yf.Ticker(ticker).info["beta"]
    except:
      print("No beta available")
      return 0.0
    
  # formula: sum of (weighted average * stock beta)
  def calculate_portfolio_beta(self):
    holdings_df = self.sql_to_pd_dataframe("holdings")
    holdings_df["beta"] = holdings_df["ticker"].apply(lambda x: self.get_stock_beta(x))
    # total cost will be in dollars
    holdings_df["total cost"] = (holdings_df["avg_price"] / 100) * holdings_df["quantity"]
    holdings_df["weighted average"] = holdings_df["total cost"] / holdings_df["total cost"].sum()
    portfolio_beta = (holdings_df["weighted average"] * holdings_df["beta"]).sum()
    self.portfolio_beta = round(portfolio_beta,2) 
    return self.portfolio_beta

# -------------------------------------------------front-end---------------------------------------------------------------------------
  def draw_stocks_diversity(self, mycursor = mycursor):
    mycursor.execute("SELECT ticker, quantity FROM holdings")
    res = mycursor.fetchall()
    quantity_stocks = [x[1] for x in res]
    ticker_stocks = [x[0] for x in res]
    fig, ax = plt.subplots()
    ax.pie(quantity_stocks, labels=ticker_stocks, autopct='%1.1f%%')
    return fig
    
  def get_stock_industry(self, stocks):

    # helper function 
    def get_industry_helper(ticker):
      try:
          return yf.Ticker(ticker).info["sector"]
      except:
          return "Unknown"
      
    industries = [get_industry_helper(ticker) for ticker in stocks]
    return industries
  
  # cleanup function to get number of stocks for each sectors
  def get_num_sectors(self, num_stocks,sectors):
    stocks_foreach_sector = {}
    for i in range(len(sectors)):
        if sectors[i] in stocks_foreach_sector.keys():
            stocks_foreach_sector[sectors[i]] += num_stocks[i]
        else:
            stocks_foreach_sector[sectors[i]] = num_stocks[i]
    return stocks_foreach_sector
  
  def draw_sectors_diversity(self, mycursor = mycursor):
    mycursor.execute("SELECT ticker, quantity FROM holdings")
    res = mycursor.fetchall()
    quantity_stocks = [x[1] for x in res]
    sector_stocks = self.get_stock_industry([x[0] for x in res])
    stocks_sector = self.get_num_sectors(quantity_stocks,sector_stocks)
    fig, ax = plt.subplots()
    ax.pie(stocks_sector.values(), labels=stocks_sector.keys(), autopct='%1.1f%%')
    return fig
  
  def get_stocks_in_holding(self, mycursor = mycursor):
    mycursor.execute("SELECT ticker FROM holdings")
    res = mycursor.fetchall()
    stocks_ticker = [x[0] for x in res]
    return stocks_ticker
  
  def get_close_price(self, start, end, mycursor = mycursor):
    stocks_ticker = self.get_stocks_in_holding(mycursor)
    stocks = yf.download(stocks_ticker, start=start,end=end)
    res = stocks.loc[:,"Adj Close"].copy()
    return res

  def portfolio_report(self):
    print(f"Portfolio Name: {self.name}")
    print(f"Portfolio AUM: ${self.AUM}")
    print("\nPortfolio Statistics:")
    print(f"Portfolio Return: {self.total_return}%")
    print(f"Portfolio Beta: {self.portfolio_beta}")
    print(f"Portfolio Profit-Loss: ${self.profit_loss}")
    print(f"Portfolio Sharpe Ratio: {self.sharpe_ratio}")
    print(f"Portfolio Expense Ratio: {self.expense_ratio}")
    print(f"Portfolio Average P/E: {self.avg_price_to_earnings}")
    #etc.