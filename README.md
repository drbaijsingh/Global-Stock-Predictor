# 🇮🇳 Intraday Stock Predictor - Indian Markets

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://drbaijsingh-stock-predictor.streamlit.app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📊 Live Demo

**Try the app live:** [https://drbaijsingh-stock-predictor.streamlit.app](https://drbaijsingh-stock-predictor.streamlit.app)

---

## 🎯 About The Project

**Intraday Stock Predictor** is an AI-powered web application that analyzes Indian stock market data in real-time and provides actionable BUY/WAIT/AVOID signals with high accuracy.

Whether you're a day trader, swing trader, or long-term investor, this tool helps you make informed decisions by combining:
- 📈 **12+ Technical Indicators**
- 🤖 **Machine Learning Predictions**
- 📊 **VWAP (Volume Weighted Average Price)**
- 🎯 **Clear Actionable Signals**

---

## ✨ Features

### 🔍 **Complete Stock Coverage**
- **200+ Indian stocks** including NIFTY 50, mid-cap, and small-cap
- Search any stock by symbol (e.g., RELIANCE, TCS, POLYCAB, HAL, DIXON)
- Real-time data from Yahoo Finance

### 📊 **Advanced Technical Analysis**
| Indicator | What It Does |
|-----------|--------------|
| **VWAP** | Volume Weighted Average Price - institutional trading level |
| **RSI** | Relative Strength Index - overbought/oversold conditions |
| **MACD** | Moving Average Convergence Divergence - momentum |
| **Moving Averages** | MA5, MA20, MA50 - trend direction |
| **Bollinger Bands** | Volatility and price levels |
| **Stochastic** | Momentum and reversal signals |
| **Price Position** | Where price sits in the 20-day range |
| **Volume Analysis** | Confirm price movements |

### 🤖 **Machine Learning Engine**
- **Random Forest Classifier** trained on historical data
- **Real-time predictions** with probability scores
- **Feature importance** analysis to explain predictions
- **Model accuracy** displayed with each prediction

### 📈 **Interactive Visualizations**
- Candlestick charts with VWAP overlay
- Moving averages (5, 20, 50 periods)
- RSI indicator with overbought/oversold levels
- Volume bars with color coding
- Support and resistance levels

### 🎯 **Clear Trading Signals**
| Signal | Meaning | Action |
|--------|---------|--------|
| 🟢 **BUY** | Strong bullish signals | Consider buying |
| 🟡 **CAUTIOUS BUY** | Mildly bullish | Wait for confirmation |
| 🟡 **WAIT** | Mixed signals | No clear direction |
| 🟠 **CAUTIOUS AVOID** | Mildly bearish | Better to stay out |
| 🔴 **AVOID** | Strong bearish signals | Avoid buying |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/drbaijsingh/stock-predictor.git
   cd stock-predictor