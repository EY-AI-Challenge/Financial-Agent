# Financial Bros - Strategic Command Center (Financial Agent Challenge)

<h1 align="center"> <img src="https://github.com/EYAIChallenge/Overview/blob/main/EY_Logo_Beam_RGB_White_Yellow.png" width="40" alt="Logo"/> AI Challenge 2026 | Financial Agent Challenge </h1>

## 🚀 Solution Overview

**Financial Bros** is a decision support platform and strategic command center designed for sophisticated investment funds. It bridges the gap between raw financial data and actionable trading decisions. The platform features an intelligent backend engine providing real-time technical analysis (Simple Moving Averages) and a premium, responsive "cyberpunk" dashboard for fund managers.

### Key Value Propositions
- **Strategic Insight Generation**: Automatically calculates 20-day and 50-day moving averages to generate Buy/Sell/Hold signals.
- **Measurable Business Impact**: Reduces analysis time, standardizes technical indicators across a diverse 11-asset portfolio, and mitigates risk through objective algorithmic recommendations.
- **Premium User Experience**: Designed with a state-of-the-art "glassmorphism" aesthetic, ensuring the tool feels like a high-value strategic asset that integrates seamlessly into a modern fund manager's workflow.

---

## 📦 How to Run the Solution

### Prerequisites
- Python 3.9+
- The required dependencies inside a virtual environment.

### 1. Setup Environment
```bash
# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install yfinance fastapi uvicorn pandas numpy scikit-learn
```

### 2. Fetch the Data
The platform requires historical financial data. Run the data loader script to fetch the `.csv` files using the `yfinance` library:
```bash
python backend/data_loader.py
```
*This will create a `data/` directory and populate it with historical data for the 11 assets.*

### 3. Start the Backend API & Frontend
Run the FastAPI server, which also serves the frontend dashboard:
```bash
python backend/main.py
```
The server will start on `http://0.0.0.0:8000`.

### 4. Access the Dashboard
Open your web browser and navigate to:
**[http://localhost:8000/](http://localhost:8000/)**

---

## 🛠️ Architecture

- **Backend (`backend/main.py`, `backend/ai_agent.py`)**: A high-performance FastAPI application. It loads `.csv` data, serves RESTful endpoints for the frontend, and runs the `ai_agent` logic (SMA crossover strategy) to generate insights.
- **Frontend (`frontend/`)**: A modern Vanilla HTML/CSS/JS web application utilizing Chart.js for data visualization and Lucide for icons. Built with dynamic, responsive CSS and no heavy frontend frameworks for maximum speed.
- **Data Engine (`backend/data_loader.py`)**: Automates the collection of Yahoo Finance historical data.

---

## 🎯 Original Challenge Description

In this challenge, your team will act as strategic consultants for a sophisticated **investment fund** seeking to leverage **AI** in its daily operations. The fund manages a **diverse portfolio** of 11 different stocks and cryptocurrencies. Your team can choose to focus on the entire portfolio, a strategic selection, or an in-depth analysis of a single high-value asset.

### **Objective**  
Your mission is to create a **decision support platform** that transforms the fund's investment capabilities. Whether designing an intelligent trading agent, a sophisticated analytical dashboard, or a hybrid solution, you must demonstrate how AI can generate **tangible business value** in financial markets.

### 💡 Data

The dataset includes **historical financial data** from different assets, for example: 
- **Stocks:** AMZN, AAPL, GOOGL, MSFT, UDMY, NXE, SPY, CDR.WA, EH  
- **Cryptocurrencies:** BTC-USD, ETH-USD  

All data is from Yahoo library (yfinance) stored in `.csv` files. 

### Data Columns:
- **Datetime / Date:** Timestamp of the market data entry (hourly or daily).
- **Close:** Price at the end of the interval.
- **High:** Highest price during the interval.
- **Low:** Lowest price during the interval.
- **Open:** Price at the beginning of the interval.
- **Volume:** Number of shares/contracts/units traded.
