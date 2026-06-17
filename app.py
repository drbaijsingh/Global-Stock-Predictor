import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf

# Import your custom modules
from data_fetcher import (
    fetch_stock_data, 
    fetch_company_info, 
    fetch_multiple_stocks,
    get_cache_status,
    is_market_open,
    get_cache_ttl
)
from model_predictor import generate_predictions, create_features
from utils import (
    format_currency,
    format_large_number,
    create_price_chart,
    calculate_metrics,
    display_cache_info
)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="📈 Stock Predictor Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STOCK LISTS ---
# Popular stocks by category
POPULAR_STOCKS = {
    "🇺🇸 US Tech Giants": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX"],
    "🇺🇸 US Banks": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
    "🇺🇸 US Healthcare": ["JNJ", "PFE", "UNH", "MRK", "ABBV", "TMO"],
    "🇺🇸 US Retail": ["WMT", "TGT", "COST", "HD", "MCD", "NKE"],
    "🇨🇳 Chinese Tech": ["BABA", "JD", "PDD", "BIDU", "TCEHY"],
    "🇪🇺 European": ["ASML", "NOVO-B.CO", "SAP", "NESN.SW", "AZN.L"],
    "🇯🇵 Japanese": ["TM", "SONY", "MUFG", "TSE:9984"],  # Toyota, Sony, etc.
    "📊 ETFs": ["SPY", "QQQ", "DIA", "VTI", "VOO", "BND"],
    "📈 Crypto-Related": ["COIN", "MSTR", "RIOT", "MARA"],
    "🔥 Trending": ["PLTR", "SNOW", "UBER", "SHOP", "SQ"]
}

# Default stocks to display on the dashboard
DEFAULT_WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]

# Major indices
INDICES = {
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "Russell 2000": "^RUT",
    "VIX": "^VIX"
}

# --- INITIALIZE SESSION STATE ---
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = 0
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "AAPL"
if 'watchlist_data' not in st.session_state:
    st.session_state.watchlist_data = {}

# --- HELPER FUNCTIONS ---
def get_stock_suggestion(query):
    """Get stock suggestions based on user input"""
    all_stocks = []
    for category, stocks in POPULAR_STOCKS.items():
        all_stocks.extend(stocks)
    all_stocks = list(set(all_stocks))  # Remove duplicates
    
    query = query.upper()
    suggestions = [s for s in all_stocks if query in s]
    return suggestions[:5]  # Return top 5 matches

def display_watchlist():
    """Display watchlist with current prices"""
    st.sidebar.subheader("📊 Watchlist")
    
    # Allow user to customize watchlist
    watchlist = st.sidebar.multiselect(
        "Select stocks to watch",
        options=list(set([stock for stocks in POPULAR_STOCKS.values() for stock in stocks])),
        default=DEFAULT_WATCHLIST
    )
    
    if watchlist:
        # Fetch data for all watchlist stocks
        with st.spinner("Loading watchlist..."):
            watchlist_data = fetch_multiple_stocks(watchlist, period="5d")
        
        if not watchlist_data.empty:
            # Display latest prices
            latest_prices = watchlist_data.iloc[-1]
            
            # Calculate daily changes
            if len(watchlist_data) > 1:
                prev_prices = watchlist_data.iloc[-2]
                changes = ((latest_prices - prev_prices) / prev_prices * 100)
            else:
                changes = pd.Series([0] * len(latest_prices), index=latest_prices.index)
            
            # Display in a clean format
            for ticker in watchlist:
                if ticker in latest_prices:
                    price = latest_prices[ticker]
                    change = changes.get(ticker, 0)
                    
                    # Color code the change
                    color = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
                    
                    # Create metric
                    st.sidebar.metric(
                        label=f"{ticker}",
                        value=f"${price:.2f}",
                        delta=f"{change:.2f}%",
                        delta_color="normal"
                    )

# --- MAIN APP ---
def main():
    # --- HEADER ---
    st.title("📈 Stock Predictor Pro")
    st.caption(f"Real-time data from Yahoo Finance • Market is {'🟢 Open' if is_market_open() else '🔴 Closed'}")
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Stock selection with categories
        st.subheader("🔍 Select Stock")
        
        # Option 1: Quick pick from categories
        category = st.selectbox(
            "Browse by Category",
            options=["-- Custom Search --"] + list(POPULAR_STOCKS.keys())
        )
        
        if category != "-- Custom Search --":
            ticker_options = POPULAR_STOCKS[category]
            selected_ticker = st.selectbox(
                "Select Stock",
                options=ticker_options,
                index=0
            )
        else:
            # Option 2: Custom search with suggestions
            search_query = st.text_input(
                "Search Stock Symbol",
                value=st.session_state.selected_ticker,
                placeholder="e.g., AAPL, TSLA, MSFT"
            )
            
            if search_query:
                suggestions = get_stock_suggestion(search_query)
                if suggestions:
                    selected_ticker = st.selectbox(
                        "Suggestions",
                        options=suggestions,
                        index=0
                    )
                else:
                    selected_ticker = search_query.upper()
            else:
                selected_ticker = st.session_state.selected_ticker
        
        # Update session state
        st.session_state.selected_ticker = selected_ticker
        
        # --- TIME PERIOD ---
        st.divider()
        st.subheader("📅 Time Period")
        period = st.selectbox(
            "Data Range",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
            index=3,
            help="Amount of historical data to analyze"
        )
        
        # --- PREDICTION SETTINGS ---
        st.divider()
        st.subheader("🔮 Prediction Settings")
        
        predict_days = st.slider(
            "Days to Predict",
            min_value=1,
            max_value=30,
            value=5,
            help="Number of future trading days to forecast"
        )
        
        use_advanced_model = st.toggle(
            "Use Advanced Model",
            value=False,
            help="Enable more complex (but slower) prediction model"
        )
        
        # --- REFRESH CONTROLS ---
        st.divider()
        st.subheader("🔄 Refresh")
        
        col1, col2 = st.columns(2)
        with col1:
            auto_refresh = st.toggle("Auto", value=True)
        with col2:
            if st.button("🔄 Now", use_container_width=True):
                st.cache_data.clear()
                st.session_state.refresh_token += 1
                st.rerun()
        
        if auto_refresh:
            ttl = get_cache_ttl()
            st.caption(f"Auto-refresh every {ttl//60} minutes")
        
        # --- WATCHLIST ---
        st.divider()
        display_watchlist()
        
        # --- CACHE STATUS ---
        st.divider()
        st.subheader("📊 Status")
        status_placeholder = st.empty()
    
    # --- MAIN CONTENT ---
    # Display current stock info
    st.header(f"📊 {selected_ticker} Analysis")
    
    # Fetch data
    df = fetch_stock_data(selected_ticker, period)
    
    # Update status
    if not df.empty:
        status_placeholder.info(get_cache_status(df))
    else:
        status_placeholder.warning("No data available")
    
    if df.empty:
        st.error(f"❌ Unable to load data for {selected_ticker}")
        st.info("💡 Tips:\n- Check the ticker symbol\n- Try a different time period\n- Search for the correct symbol")
        
        # Show similar stocks
        similar = get_stock_suggestion(selected_ticker[:3])
        if similar:
            st.write("Did you mean:", ", ".join(similar))
        return
    
    # --- METRICS ROW ---
    metrics = calculate_metrics(df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Current Price",
            format_currency(metrics.get('current_price', 0)),
            delta=f"{metrics.get('price_change_pct', 0):.2f}%",
            help="Latest closing price with daily change"
        )
    
    with col2:
        st.metric(
            "52-Week High",
            format_currency(metrics.get('high_52w', 0)),
            help="Highest price in the last 52 weeks"
        )
    
    with col3:
        st.metric(
            "52-Week Low",
            format_currency(metrics.get('low_52w', 0)),
            help="Lowest price in the last 52 weeks"
        )
    
    with col4:
        avg_vol = metrics.get('avg_volume', 0)
        st.metric(
            "Avg Volume",
            f"{int(avg_vol):,}" if avg_vol else "N/A",
            help="Average daily trading volume"
        )
    
    with col5:
        position = metrics.get('high_52w_pct', 0)
        st.metric(
            "52-Week Position",
            f"{position:.1f}%" if position else "N/A",
            help="Current price position within 52-week range"
        )
    
    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Chart", "📊 Technicals", "🔮 Predictions", "ℹ️ Company Info"])
    
    with tab1:
        # Generate predictions
        predictions = None
        if predict_days > 0:
            with st.spinner("🔮 Generating predictions..."):
                try:
                    predictions = generate_predictions(df, predict_days)
                except Exception as e:
                    st.warning(f"Prediction error: {str(e)}")
        
        # Create chart
        fig = create_price_chart(df, predictions)
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional chart options
        col1, col2 = st.columns(2)
        with col1:
            show_volume = st.checkbox("Show Volume", value=True)
            if show_volume and not df.empty:
                st.bar_chart(df['Volume'].tail(60))
        
        with col2:
            show_ma = st.checkbox("Show Moving Averages", value=False)
            if show_ma and not df.empty:
                ma_data = pd.DataFrame({
                    'SMA 20': df['Close'].rolling(20).mean(),
                    'SMA 50': df['Close'].rolling(50).mean(),
                    'Close': df['Close']
                }).tail(100)
                st.line_chart(ma_data)
        
        # Raw data
        with st.expander("📋 View Raw Data"):
            st.dataframe(df.tail(20), use_container_width=True)
            st.download_button(
                label="📥 Download CSV",
                data=df.tail(100).to_csv(),
                file_name=f"{selected_ticker}_data.csv",
                mime="text/csv"
            )
    
    with tab2:
        st.subheader("📊 Technical Indicators")
        
        # Technical indicators from model_predictor
        if len(df) > 30:
            features = create_features(df)
            
            # Display key indicators
            col1, col2 = st.columns(2)
            
            with col1:
                # RSI
                from model_predictor import calculate_rsi
                rsi = calculate_rsi(df['Close'])
                st.subheader("RSI (Relative Strength Index)")
                st.line_chart(rsi.tail(100))
                
                # Volume
                st.subheader("Volume")
                st.bar_chart(df['Volume'].tail(60))
            
            with col2:
                # Volatility
                if 'Daily_Return' in features.columns:
                    st.subheader("Daily Returns")
                    st.line_chart(features['Daily_Return'].tail(100))
                
                # Moving Average Convergence/Divergence (MACD) - simplified
                if len(df) > 26:
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    macd = exp1 - exp2
                    signal = macd.ewm(span=9, adjust=False).mean()
                    
                    macd_data = pd.DataFrame({
                        'MACD': macd.tail(100),
                        'Signal': signal.tail(100)
                    })
                    st.subheader("MACD")
                    st.line_chart(macd_data)
        else:
            st.info("Need at least 30 days of data for technical indicators")
    
    with tab3:
        st.subheader("🔮 Price Predictions")
        
        if predictions is not None and not predictions.empty:
            # Display predictions
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Predicted Price (Day 1)",
                    format_currency(predictions.iloc[0]['Predicted_Close']),
                    delta=f"{((predictions.iloc[0]['Predicted_Close'] - metrics.get('current_price', 0)) / metrics.get('current_price', 1) * 100):.2f}%"
                )
            
            with col2:
                st.metric(
                    f"Predicted Price (Day {predict_days})",
                    format_currency(predictions.iloc[-1]['Predicted_Close']),
                    delta=f"{((predictions.iloc[-1]['Predicted_Close'] - metrics.get('current_price', 0)) / metrics.get('current_price', 1) * 100):.2f}%"
                )
            
            # Full prediction table
            pred_df = predictions.copy()
            pred_df['Predicted_Close'] = pred_df['Predicted_Close'].apply(lambda x: format_currency(x))
            st.dataframe(pred_df, use_container_width=True)
            
            # Confidence intervals (placeholder)
            st.info("📊 Prediction confidence: Moderate (based on historical patterns)")
        else:
            st.warning("⚠️ Unable to generate predictions. Ensure you have at least 30 days of historical data.")
        
        # Model explanation
        with st.expander("ℹ️ About the Prediction Model"):
            st.markdown("""
            **How predictions work:**
            - Uses Random Forest Regressor
            - Trained on historical price patterns
            - Considers: Price, Volume, Volatility, Momentum
            - Predictions are for educational purposes only
            
            **Limitations:**
            - Not financial advice
            - Market conditions can change rapidly
            - Past performance doesn't guarantee future results
            """)
    
    with tab4:
        st.subheader("🏢 Company Information")
        
        info = fetch_company_info(selected_ticker)
        
        if info:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**📌 Basic Info**")
                st.write(f"**Name:** {info.get('name', 'N/A')}")
                st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                st.write(f"**Industry:** {info.get('industry', 'N/A')}")
            
            with col2:
                st.write("**💰 Financials**")
                st.write(f"**Market Cap:** {format_large_number(info.get('market_cap', 0))}")
                st.write(f"**P/E Ratio:** {info.get('pe_ratio', 'N/A')}")
                st.write(f"**Dividend Yield:** {info.get('dividend_yield', 'N/A')}")
            
            with col3:
                st.write("**📈 Price Range**")
                st.write(f"**52-Week High:** {format_currency(info.get('52_week_high', 0))}")
                st.write(f"**52-Week Low:** {format_currency(info.get('52_week_low', 0))}")
        else:
            st.info(f"Company information not available for {selected_ticker}")
        
        # News (placeholder)
        st.subheader("📰 Recent News")
        st.info("News integration coming soon!")

    # --- FOOTER ---
    st.divider()
    st.caption("📊 Data provided by Yahoo Finance | Built with Streamlit | For educational purposes only")

# --- RUN APP ---
if __name__ == "__main__":
    main()