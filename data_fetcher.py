import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

# --- Configuration ---
CACHE_TTL = 3600  # 1 hour default
MARKET_TTL = 300   # 5 minutes during market hours

def is_market_open():
    """Check if US stock market is currently open"""
    try:
        now = datetime.now(pytz.timezone('US/Eastern'))
        if now.weekday() >= 5:  # Weekend
            return False
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now <= market_close
    except:
        return False

def get_cache_ttl():
    """Return appropriate TTL based on market status"""
    return MARKET_TTL if is_market_open() else CACHE_TTL

@st.cache_data(ttl=get_cache_ttl(), show_spinner="Fetching stock data...")
def fetch_stock_data(ticker, period="1y", interval="1d"):
    """
    Fetch stock data with dynamic caching.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            st.warning(f"No data found for {ticker}")
            return pd.DataFrame()
        
        # Store metadata
        df.attrs['fetch_time'] = datetime.now()
        df.attrs['ticker'] = ticker
        df.attrs['period'] = period
        df.attrs['market_open'] = is_market_open()
        df.attrs['data_source'] = 'yfinance'
        
        # Data cleaning
        df = clean_stock_data(df)
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=86400)  # 24 hours
def fetch_company_info(ticker):
    """Fetch company information - cached for a day"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            return {}
        
        # Extract relevant information
        return {
            'name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            '52_week_high': info.get('fiftyTwoWeekHigh', 0),
            '52_week_low': info.get('fiftyTwoWeekLow', 0),
        }
    except:
        return {}

@st.cache_data(ttl=3600)
def fetch_multiple_stocks(tickers, period="1mo"):
    """Fetch data for multiple stocks at once"""
    data = {}
    for ticker in tickers:
        try:
            df = fetch_stock_data(ticker, period)
            if not df.empty and 'Close' in df.columns:
                data[ticker] = df['Close']
        except:
            continue
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def clean_stock_data(df):
    """Clean and validate stock data"""
    try:
        # Forward fill missing values
        df = df.ffill()
        
        # Backward fill any remaining missing values
        df = df.bfill()
        
        # Remove any rows with all NaN
        df = df.dropna(how='all')
        
        # Check for unrealistic values
        if not df.empty:
            # Remove rows where volume is negative
            if 'Volume' in df.columns:
                df = df[df['Volume'] >= 0]
            
            # Remove rows where price is 0 or negative
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in df.columns:
                    df = df[df[col] > 0]
        
        return df
    except:
        return df

def get_cache_status(df):
    """Get human-readable cache status"""
    if df.empty:
        return "No data available"
    
    try:
        fetch_time = df.attrs.get('fetch_time', datetime.now())
        time_since = (datetime.now() - fetch_time).total_seconds() / 60
        
        if time_since < 1:
            return "🔄 Just fetched"
        elif time_since < 60:
            return f"✅ Cached ({int(time_since)} min ago)"
        else:
            hours = int(time_since / 60)
            minutes = int(time_since % 60)
            return f"⏰ Cached ({hours}h {minutes}m ago)"
    except:
        return "Cache status unavailable"