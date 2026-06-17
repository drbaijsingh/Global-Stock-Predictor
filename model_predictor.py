import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

@st.cache_resource
def load_or_create_model():
    """
    Load existing model or create a new one.
    Using @st.cache_resource ensures the model is loaded only once.
    """
    model_path = 'models/stock_predictor.pkl'
    scaler_path = 'models/scaler.pkl'
    
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            return model, scaler
        except:
            # If loading fails, create new model
            pass
    
    # Create default model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    scaler = StandardScaler()
    return model, scaler

@st.cache_data(ttl=3600)  # Cache predictions for 1 hour
def generate_predictions(df, days_ahead=5):
    """
    Generate stock price predictions.
    
    Parameters:
    - df: Historical stock data
    - days_ahead: Number of days to predict
    
    Returns:
    - DataFrame with predictions
    """
    if df.empty or len(df) < 30:
        return pd.DataFrame()
    
    try:
        # Prepare features
        df_features = create_features(df)
        
        if df_features.empty or len(df_features) < 30:
            return pd.DataFrame()
        
        # Load model
        model, scaler = load_or_create_model()
        
        # Prepare data for training
        X = df_features.drop('Target', axis=1).values if 'Target' in df_features.columns else df_features.values
        y = df['Close'].shift(-1).dropna().values[:len(df_features)]
        
        # Ensure X and y have same length
        min_len = min(len(X), len(y))
        X = X[:min_len]
        y = y[:min_len]
        
        if len(X) < 30:
            return pd.DataFrame()
        
        # Scale features
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model.fit(X_scaled, y)
        
        # Save model
        joblib.dump(model, 'models/stock_predictor.pkl')
        joblib.dump(scaler, 'models/scaler.pkl')
        
        # Make predictions for future days
        predictions = []
        last_sequence = X_scaled[-1:].copy()
        
        for i in range(days_ahead):
            # Predict next day
            next_price = model.predict(last_sequence)[0]
            predictions.append(next_price)
            
            # Update sequence (simple approach - shift and add)
            # This is simplified; in practice you'd update with predicted values
            new_row = last_sequence[0].copy()
            # Replace last feature with predicted price effect
            # You might need to adjust based on your actual features
            last_sequence = np.array([new_row])
        
        # Create prediction dates
        last_date = df.index[-1]
        pred_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days_ahead)
        
        # Create prediction DataFrame
        pred_df = pd.DataFrame({
            'Date': pred_dates,
            'Predicted_Close': predictions
        })
        pred_df.set_index('Date', inplace=True)
        
        return pred_df
        
    except Exception as e:
        st.error(f"Error generating predictions: {str(e)}")
        return pd.DataFrame()

def create_features(df):
    """
    Create technical indicators for the model.
    Fixed version - creates all features properly.
    """
    try:
        # Make a copy to avoid modifying original
        df_features = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        
        # --- PRICE-BASED FEATURES ---
        # Simple Moving Averages
        df_features['SMA_5'] = df['Close'].rolling(window=5).mean()
        df_features['SMA_10'] = df['Close'].rolling(window=10).mean()
        df_features['SMA_20'] = df['Close'].rolling(window=20).mean()
        df_features['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df_features['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df_features['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # --- MOMENTUM FEATURES ---
        # Daily Returns (FIX: Created first, then used for volatility)
        df_features['Daily_Return'] = df['Close'].pct_change()
        
        # Volatility (Now 'Daily_Return' exists)
        df_features['Volatility_5'] = df_features['Daily_Return'].rolling(window=5).std()
        df_features['Volatility_10'] = df_features['Daily_Return'].rolling(window=10).std()
        df_features['Volatility_20'] = df_features['Daily_Return'].rolling(window=20).std()
        
        # Momentum (rate of change)
        df_features['Momentum_5'] = df['Close'] - df['Close'].shift(5)
        df_features['Momentum_10'] = df['Close'] - df['Close'].shift(10)
        df_features['Momentum_20'] = df['Close'] - df['Close'].shift(20)
        
        # Rate of Change
        df_features['ROC_5'] = ((df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5)) * 100
        df_features['ROC_10'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        
        # --- VOLUME FEATURES ---
        # Volume Moving Averages
        df_features['Volume_SMA_5'] = df['Volume'].rolling(window=5).mean()
        df_features['Volume_SMA_10'] = df['Volume'].rolling(window=10).mean()
        
        # Volume Ratio (current volume / average volume)
        df_features['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
        
        # --- PRICE RANGE FEATURES ---
        # High-Low range
        df_features['HL_Range'] = (df['High'] - df['Low']) / df['Close'] * 100
        
        # High-Open range
        df_features['HO_Range'] = (df['High'] - df['Open']) / df['Open'] * 100
        
        # Open-Close range
        df_features['OC_Range'] = (df['Close'] - df['Open']) / df['Open'] * 100
        
        # --- RSI ---
        df_features['RSI'] = calculate_rsi(df['Close'])
        
        # --- MACD ---
        macd, signal = calculate_macd(df['Close'])
        df_features['MACD'] = macd
        df_features['MACD_Signal'] = signal
        
        # --- PRICE POSITION ---
        # Position in 52-week range
        high_52w = df['High'].rolling(window=252).max()  # 252 trading days in a year
        low_52w = df['Low'].rolling(window=252).min()
        df_features['High_52w'] = high_52w
        df_features['Low_52w'] = low_52w
        df_features['52w_Position'] = ((df['Close'] - low_52w) / (high_52w - low_52w)) * 100
        
        # --- TARGET (for training) ---
        # Future return (used as target)
        df_features['Target'] = df['Close'].shift(-1) - df['Close']
        
        # Drop NaN values (created by rolling windows)
        df_features = df_features.dropna()
        
        return df_features
        
    except Exception as e:
        st.error(f"Error creating features: {str(e)}")
        return pd.DataFrame()

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Avoid division by zero
        rs = gain / loss.where(loss != 0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except:
        return pd.Series(index=prices.index)

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    try:
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line
    except:
        return pd.Series(index=prices.index), pd.Series(index=prices.index)