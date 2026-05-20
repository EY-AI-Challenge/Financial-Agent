# Financial Decision Support Platform - Frontend

## Overview
Modern React application with a premium dark-mode aesthetic, built with Vite, Tailwind CSS, and React Router.

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.jsx          # Main layout wrapper with Sidebar + Navbar
│   │   ├── Navbar.jsx          # Top navigation bar
│   │   └── Sidebar.jsx         # Left sidebar with navigation & watchlist
│   ├── pages/
│   │   ├── Dashboard.jsx       # Portfolio overview & market insights
│   │   ├── AssetDetails.jsx    # Individual asset details & charts
│   │   ├── InvestmentSimulator.jsx  # Portfolio simulator
│   │   └── SmartAdvisor.jsx    # AI recommendations
│   ├── services/
│   │   └── api.js              # Axios API client
│   ├── store/
│   │   └── index.js            # State management placeholder
│   ├── App.jsx                 # Main app with routing
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
├── package.json
├── vite.config.js
├── tailwind.config.js
├── Dockerfile
└── index.html
```

## 🚀 Getting Started

### Prerequisites
- Node.js 20+
- npm or yarn

### Installation & Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server (runs on http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📦 Tech Stack

- **Framework**: React 18
- **Bundler**: Vite 5
- **Routing**: React Router 6
- **Styling**: Tailwind CSS + Custom CSS
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Icons**: Lucide React
- **Development**: ESLint

## 🎨 Design Features

- **Dark Mode**: Premium dark theme (bg-dark-900, dark-800, dark-700)
- **Glassmorphism**: Frosted glass effect with transparency and blur
- **Responsive**: Mobile-first responsive design
- **Accent Colors**: Blue (#3b82f6), Green (#10b981), Red (#ef4444)

## 📄 Pages

### 1. Dashboard (`/`)
- Portfolio overview cards
- 24-hour market changes
- Market insights
- AI recommendations preview

### 2. Asset Details (`/assets/:ticker`)
- Price history chart placeholder
- 52-week highs/lows
- 1-week, 1-month, 1-year predictions
- Historical data visualization

### 3. Investment Simulator (`/simulator`)
- Configure initial investment
- Select time horizon (1w, 1m, 1y)
- Choose assets for portfolio
- View projected returns
- Suggested allocation percentage

### 4. Smart Advisor (`/advisor`)
- Risk tolerance selector (Low/Medium/High)
- AI-powered buy/sell/hold recommendations
- Confidence scores for each recommendation
- Portfolio health metrics

## 🔌 API Integration

The app includes a configured Axios client (`src/services/api.js`) with:
- Base URL: `http://localhost:8000/api`
- JWT token management
- Request/response interceptors
- Predefined API methods:
  - `auth.register()` / `auth.login()`
  - `data.getHistory()` / `data.getTickers()`
  - `predictions.getTickerPredictions()`
  - `advisor.getRecommendations()`

## 🐳 Docker Support

```bash
# Build Docker image
docker build -t financial-frontend .

# Run container
docker run -p 3000:3000 financial-frontend
```

## 🎯 Next Steps

1. Connect API endpoints to real backend
2. Add Recharts for interactive price charts
3. Implement authentication pages (Login/Register)
4. Add real-time WebSocket updates
5. Enhance responsive design for mobile
6. Add loading states and error handling

## 📝 Notes

- Proxy configured in `vite.config.js` to forward `/api` requests to backend
- Tailwind CSS custom theme defined in `tailwind.config.js`
- Component styling uses utility classes + custom `.glass-effect` and button classes
