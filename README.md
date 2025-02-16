📌 TradingBot Collection - Algorithmic Trading Bots
Author: Frederik Urban

Welcome to the TradingBot Collection, a set of algorithmic trading bots developed in Python and integrated with MetaTrader 5 (MT5). These bots are designed for automated trading, including scalping, swing trading, and hybrid strategies.

📜 Table of Contents
About the Project
Features
Installation
Usage
Configuration
Backtesting and Analysis
Trading Strategies
Performance Results
License
🚀 About the Project
This repository contains multiple versions of trading bots, each tailored for different market conditions and strategies. These bots leverage MetaTrader 5 (MT5) API to execute trades based on technical indicators and price action.

🛠 Features
✔️ Fully Automated Trading – Executes trades without manual intervention
✔️ Backtesting Capabilities – Includes historical testing scripts
✔️ Stop Loss & Take Profit Management – Implements risk control measures
✔️ Trend Following & Reversal Strategies – Supports different trading styles
✔️ Multiple Timeframe Analysis – Adapts to various market conditions
✔️ Logging & Performance Tracking – Provides real-time trade insights

📦 Installation
Requirements
Python 3.8+
MetaTrader 5 (pip install MetaTrader5)
Pandas (pip install pandas)
Pytz (pip install pytz)
TA-Lib (Optional, for advanced indicators)

🔬 Backtesting and Analysis
This repository includes multiple Jupyter Notebooks and scripts for backtesting trading strategies:

statistic.ipynb – Statistical analysis of trade performance
plot.ipynb – Visualization of backtesting results
how-to-backtest-3-in-a-row-candles.ipynb – Example strategy for candlestick pattern backtesting
aa.ipynb & test.ipynb – Additional testing and research scripts

📊 Trading Strategies
1️⃣ Trend-Following Strategy
Uses Simple Moving Averages (SMA) to determine trend direction.
Buy Signal: Price crosses above SMA.
Sell Signal: Price crosses below SMA.

2️⃣ Scalping Strategy
Short-term trades based on price action and volatility.
Stop-Loss: Dynamic SL adjustment based on ATR levels.

3️⃣ Hybrid Strategy
Combines technical indicators & price action for high-probability trades.

📈 Performance Results
Example of recent trading performance on FTMO demo account:

Win Rate: 87.1%
Profit Factor: 1.08
Sharpe Ratio: 0.08
Total Trades: 403
More performance data will be updated over time.

📜 License
This project is licensed under the MIT License – feel free to modify and distribute it.

📬 Contact & Contributions
If you have any questions or want to contribute, feel free to open an issue or pull request.
