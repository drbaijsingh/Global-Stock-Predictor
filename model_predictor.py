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
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        return model, scaler
    else:
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
        # Load model
        model, scaler = load_or_create_model()
        
        # Prepare features
        df_features = create_features(df)
        
        # Get the last N days for prediction
        last_sequence = df_features.iloc[-30:].values
        
        # Scale features
        scaled_features = scaler.transform(last_sequence)
        
        # Make predictions
        predictions = []
        current_sequence = scaled_features.copy()
        
        for _ in range(days_ahead):
            # Predict next day
            next_price = model.predict(current_sequence[-1].reshape(1, -1))[0]
            predictions.append(next_price)
            
            # Update sequence (shift and add prediction)
            new_row = current_sequence[-1].copy()
            # Update the last row with predicted values
            # This is simplified - you'll need to adapt based on your features
            current_sequence = np.vstack([current_sequence, new_row])
        
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
    """
    df_features = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # Price-based features
    df_features['SMA_5'] = df['Close'].rolling(window=5).mean()
    df_features['SMA_20'] = df['Close'].rolling(window=20).mean()
    df_features['RSI'] = calculate_rsi(df['Close'])
    
    # Volatility features
    df_features['Daily_Return'] = df['Close'].pct_change()
    df_features['Volatility_5'] = df['Daily_Return'].rolling(window=5).std()
    
    # Momentum features
    df_features['Momentum_5'] = df['Close'] - df['Close'].shift(5)
    df_features['Momentum_10'] = df['Close'] - df['Close'].shift(10)
    
    # Volume features
    df_features['Volume_SMA'] = df['Volume'].rolling(window=5).mean()
    df_features['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
    
    # Drop NaN values
    df_features = df_features.dropna()
    
    return df_features

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi