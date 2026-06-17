import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

def format_currency(value):
    """Format value as currency"""
    try:
        return f"${value:,.2f}"
    except:
        return "N/A"

def format_large_number(value):
    """Format large numbers with K, M, B suffixes"""
    try:
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        elif value >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:,.2f}"
    except:
        return "N/A"

def create_price_chart(df, predictions=None):
    """Create interactive price chart with predictions"""
    fig = go.Figure()
    
    if not df.empty and 'Close' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Close'],
            mode='lines',
            name='Historical',
            line=dict(color='blue', width=2)
        ))
    
    if predictions is not None and not predictions.empty:
        fig.add_trace(go.Scatter(
            x=predictions.index,
            y=predictions['Predicted_Close'],
            mode='lines+markers',
            name='Predicted',
            line=dict(color='red', width=2, dash='dash'),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title='Stock Price Chart',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

def calculate_metrics(df):
    """Calculate key stock metrics"""
    if df.empty:
        return {}
    
    try:
        last_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2] if len(df) > 1 else last_close
        price_change = last_close - prev_close
        price_change_pct = (price_change / prev_close) * 100 if prev_close != 0 else 0
        
        high_52w = df['High'].max() if 'High' in df.columns else None
        low_52w = df['Low'].min() if 'Low' in df.columns else None
        
        return {
            'current_price': last_close,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'avg_volume': df['Volume'].mean() if 'Volume' in df.columns else None,
            'high_52w_pct': ((last_close - low_52w) / (high_52w - low_52w) * 100) if high_52w and low_52w else None
        }
    except:
        return {}

def display_cache_info(df):
    """Display cache status in sidebar"""
    if df.empty:
        st.info("No data loaded")
        return
    
    try:
        fetch_time = df.attrs.get('fetch_time', datetime.now())
        market_open = df.attrs.get('market_open', False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Last Updated", fetch_time.strftime("%H:%M:%S"))
        with col2:
            st.metric("Market Status", "🟢 Open" if market_open else "🔴 Closed")
        
        time_since = (datetime.now() - fetch_time).total_seconds() / 60
        st.caption(f"Data updated {int(time_since)} minutes ago")
    except:
        st.info("Cache status unavailable")