# 💰 Financial Decision Support Platform

An AI-powered investment platform built for the **EY AI Challenge** hackathon. Built with React, FastAPI, PostgreSQL, and ML models for intelligent financial recommendations.

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker & Docker Compose installed
- ~2GB free disk space
- 4+ GB RAM

### Start the Platform

```bash
docker-compose up
```

Done! Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

---

## 📋 Project Structure

```
Financial-Agent/
├── frontend/                    # React + Vite + Tailwind
│   ├── src/
│   │   ├── pages/              # 4 main pages
│   │   ├── components/         # Reusable UI components
│   │   ├── services/           # API client
│   │   └── App.jsx
│   ├── Dockerfile              # Multi-stage: dev + prod
│   └── package.json
│
├── backend/                    # FastAPI + SQLAlchemy
│   ├── main.py                 # API routes
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile
│
├── financial_data/             # Historical CSV data
│   ├── AAPL.csv
│   ├── GOOGL.csv
│   └── ... (11 tickers)
│
├── docker-compose.yml          # Production config
├── docker-compose.dev.yml      # Development config
├── startup.bat                 # Windows quick start
├── startup.sh                  # Linux/macOS quick start
├── DOCKER.md                   # Full Docker guide
└── README.md                   # This file
```

---

## 🏗️ Architecture

### Frontend (React 18 + Vite)
- **Routing**: React Router v6 (4 main pages)
- **Styling**: Tailwind CSS with dark theme & glassmorphism
- **State**: Context API + Axios
- **Features**: Responsive, real-time updates, interactive charts

### Backend (FastAPI)
- **Framework**: FastAPI with async/await
- **Authentication**: JWT-based with refresh tokens
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Docs**: Auto-generated Swagger/OpenAPI at `/docs`

### Database (PostgreSQL)
- **User Accounts**: Registration & authentication
- **Market Data**: Historical prices for 11 tickers
- **Predictions**: ML model outputs (1-week, 1-month, 1-year)
- **Portfolios**: User investment simulations

### ML Model (TBD)
- **Algorithm**: XGBoost or LSTM (decision pending)
- **Task**: Time-series forecasting for financial prices
- **Predictions**: 3 horizons per ticker

---

## 📊 Core Features

### 1. **Dashboard**
- Portfolio overview with total value
- 24-hour gains/losses
- Market insights (S&P 500, Bitcoin, Tech sector)
- AI recommendations preview

### 2. **Asset Details** (`/assets/:ticker`)
- Historical price chart
- 52-week high/low
- 1-week, 1-month, 1-year price predictions
- Interactive data visualization

### 3. **Investment Simulator**
- Configure initial investment amount
- Select time horizon (1-7 days, 1-30 days, 1 year)
- Choose assets to simulate
- View projected returns
- Portfolio allocation suggestions

### 4. **Smart Advisor**
- Risk tolerance selector (Low/Medium/High)
- AI-powered recommendations (Buy/Sell/Hold)
- Confidence scores for each recommendation
- Portfolio health metrics (diversification, risk score, expected return)

---

## 📡 API Endpoints

### Authentication
```
POST   /api/auth/register       # Create new user account
POST   /api/auth/login          # Get JWT token
POST   /api/auth/refresh        # Refresh access token
```

### Data Management
```
GET    /api/data/tickers        # List all available tickers
GET    /api/data/history/{ticker}  # Historical price data
POST   /api/data/ingest         # Import CSV data to database
```

### Predictions
```
GET    /api/predict/{ticker}    # 1-week, 1-month, 1-year predictions
POST   /api/predict/portfolio   # Multi-asset predictions
```

### Smart Advisor
```
POST   /api/advisor/recommendation  # Get AI recommendations
POST   /api/advisor/risk-assessment # Portfolio risk analysis
```

Full API documentation available at `http://localhost:8000/docs` (Swagger UI)

---

## 📦 Tech Stack

### Frontend
- React 18
- Vite (fast build tool)
- React Router v6
- Tailwind CSS
- Recharts (charting)
- Axios (HTTP client)
- Lucide React (icons)

### Backend
- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy (ORM)
- Pydantic (validation)
- PostgreSQL 15
- yfinance (financial data)
- XGBoost or LSTM (ML model)

### DevOps
- Docker & Docker Compose
- Multi-stage builds (production-optimized)
- Health checks & networking

---

## 🔐 Security

- **JWT Authentication**: Access + refresh tokens
- **Password Hashing**: bcrypt with salt
- **Database**: Encrypted passwords, secure credentials
- **CORS**: Configured for cross-origin requests
- **Environment Variables**: Sensitive data in `.env`

---

## 🎯 Supported Tickers

The platform includes historical data and supports predictions for:

- **Stocks**: AAPL, GOOGL, MSFT, AMZN, UDMY, NXE, SPY, CDR.WA, EH
- **Crypto**: BTC-USD, ETH-USD

---

## 🛠️ Development

### Without Docker (Local Setup)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### With Docker (Recommended)
```bash
# Development mode with hot reload
./startup.sh dev

# Or production mode
./startup.sh
```

---

## 📚 Documentation

- [DOCKER.md](DOCKER.md) - Complete Docker guide, commands, troubleshooting
- [frontend/README.md](frontend/README.md) - Frontend architecture & components
- [API Endpoints](#-api-endpoints) - Full endpoint reference
- [Architecture](#-architecture) - System design overview

---

## 📝 Development Log

- **2026-05-20**: Initial project structure, React frontend setup, Docker configuration

See [history.md](history.md) for detailed development history.

---

## 🚀 Deployment

### Production Build
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Clean Up (Remove volumes)
```bash
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

### Docker Issues
See [DOCKER.md](DOCKER.md) for detailed troubleshooting guide.

### Frontend Not Updating
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

---

## 📄 API Endpoints Reference

### Authentication
- `POST /api/auth/register`: Register a new user.
- `POST /api/auth/login`: Authenticate and return JWT token.
- `POST /api/auth/refresh`: Refresh access token.

### Data & Insights
- `GET /api/data/tickers`: Get list of available tickers.
- `GET /api/data/history/{ticker}`: Get historical data for a specific ticker.
- `POST /api/data/ingest`: Ingest CSV data into database.

### Predictions
- `GET /api/predict/{ticker}`: Get price predictions (1w, 1m, 1y) for a ticker.
- `POST /api/predict/portfolio`: Get predictions for entire portfolio.

### Smart Advisor
- `POST /api/advisor/recommendation`: Get AI-powered investment recommendations.
- `POST /api/advisor/risk-assessment`: Analyze portfolio risk.

---

## 👥 Contributors

Built during the **EY AI Challenge 2026** Hackathon

---

## 📄 License

MIT
