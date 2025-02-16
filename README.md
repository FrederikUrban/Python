# 📌 Trading Bots & HFT Arbitrage Collection
**Author:** Frederik Urban  
**License:** MIT  

Welcome to the **Trading Bots & HFT Arbitrage Collection**, a repository of algorithmic trading bots developed in **Python**. This repository is organized into two main directories:

- **HFT-Arbitrage:** Contains the most recent high-frequency trading and arbitrage strategies optimized for low-latency order execution across multiple exchanges.
- **Trading-Algorithms:** Contains earlier trading bot implementations and backtesting tools for various strategies such as trend-following, scalping, and hybrid approaches.

---

## 🚀 About the Project

This project provides a comprehensive set of trading bot implementations. The latest innovations reside in the **HFT-Arbitrage** folder, where you’ll find state-of-the-art HFT code that leverages asynchronous programming, advanced logging, and real-time market data processing. The **Trading-Algorithms** folder houses proven trading strategies along with analytical and backtesting scripts.

---

## 🛠 Features

- **High-Frequency Trading & Arbitrage:** Ultra-low latency order execution using async I/O.
- **Real-Time Market Data:** Processes live data from Binance and Bybit.
- **Multiple Trading Strategies:** Includes HFT arbitrage, trend-following, scalping, and hybrid methods.
- **Robust Logging & Error Handling:** Detailed logging for monitoring and troubleshooting.
- **Backtesting & Analysis Tools:** Scripts and notebooks for historical performance evaluation.

---

## 📦 Installation

### Requirements
- **Python 3.8+**
- **uvloop:**  
  `pip install uvloop==0.21.0`
- **orjson:**  
  `pip install orjson==3.10.15`
- **aiohttp:**  
  `pip install aiohttp==3.11.12`
- **unicorn_binance_websocket_api:**  
  `pip install unicorn_binance_websocket_api==2.9.0`
- **pybit:**  
  `pip install pybit==5.9.0`
- **termcolor:**  
  `pip install termcolor==2.5.0`

### Setup
1. **Clone the repository:**
   ```sh
   git clone https://github.com/FrederikUrban/Python.git
   cd Python
2. **Repository Structure:**
   ```sh
    Python/
    ├── HFT-Arbitrage/          # Contains the most recent HFT and arbitrage trading bots
    └── Trading-Algorithms/     # Contains earlier trading bot implementations and backtesting tools
3. Install Dependencies:
   ```sh
    pip install -r requirements.txt
   
## 🔬 Backtesting and Analysis
The Trading-Algorithms folder includes various scripts and Jupyter Notebooks for backtesting trading strategies and analyzing performance. These tools can help you simulate historical scenarios and fine-tune your approach.

## 📊 Trading Strategies
HFT Arbitrage: Exploits market inefficiencies with ultra-low latency and optimized order execution.
Trend-Following Strategy: Uses moving averages and technical indicators to capture market trends.
Scalping Strategy: Executes rapid trades to benefit from small price movements.
Hybrid Strategy: Combines multiple technical signals for high-probability trade entries.
