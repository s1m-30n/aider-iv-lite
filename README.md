# 🚀 Aider Lite: The Boom & Crash Hunter

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![MetaTrader 5](https://img.shields.io/badge/MetaTrader_5-Integration-green?style=for-the-badge&logo=windows)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Aider Lite** is your intelligent companion for dominating the Deriv **Boom** and **Crash** markets. It doesn't just guess; it analyzes, strategizes, and strikes with precision! 🎯

Whether you're looking for quick **Scalps**, juicy **Swings**, or riding the massive **Trends**, Aider Lite has got your back.

---

## ✨ Features

- **🧠 Top-Down "Cascading" Analysis**: We don't just look at one chart. We analyze **D1, H4, H1, M15, and M5** simultaneously to find the perfect alignment.
- **🌊 Trend Surfing**: Uses **EMA 50** and **MACD** to determine the market bias. We never swim against the tide!
- **🛡️ Smart Logic**:
  - **Boom**: Strictly hunts for **SELL** opportunities.
  - **Crash**: Strictly hunts for **BUY** opportunities.
- **⚡ Multi-Mode Trading**:
  - **Trend Mode**: Follows the big money.
  - **Swing Mode**: Catches the pullbacks.
  - **Scalp Mode**: Snipes the quick profits.
- **🔮 Spike Predictor** _(Coming Soon)_: Uses statistical and technical magic to warn you before a spike hits!
- **🤖 Fully Automated**: Connects directly to your MT5 terminal to place orders, set SL/TP, and manage trades.

## 🛠️ Tech Stack

- **Python**: The brain.
- **MetaTrader 5 (MT5)**: The execution arm.
- **TA-Lib**: The technical wizardry. (Click to see the [installation guide](https://blog.quantinsti.com/install-ta-lib-python/))
- **Pandas**: The data cruncher.

## 🚀 Getting Started

1.  **Clone the Repo**:

    ```bash
    git clone https://github.com/simple-codes22/aider-lite.git
    cd aider-lite
    ```

2.  **Install Dependencies**:
    We recommend using `uv` for lightning-fast installs, but `pip` works too!

    ```bash
    uv sync
    ```

3.  **Configure Secrets**:
    Create a `.env` file in the root directory:

    ```env
    LOGIN=your_mt5_login_id
    PASSWORD=your_mt5_password
    SERVER=your_mt5_server
    ```

4.  **Launch the Bot**:
    Make sure your MT5 terminal is open and "Algo Trading" is enabled!
    ```bash
    uv run main.py
    ```

## ⚠️ Disclaimer

**Trading involves risk.** This bot is a tool, not a guarantee of profit. Always test on a Demo account first! I am not responsible for any blown accounts (but I'll celebrate your wins! 🎉).

---

_Happy Trading!_ 📈
