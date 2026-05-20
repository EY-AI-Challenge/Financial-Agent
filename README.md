# Financial Decision Support Platform

## API Endpoints

### Authentication
- `POST /api/auth/register`: Register a new user.
- `POST /api/auth/login`: Authenticate and return JWT token.

### Data & Insights
- `GET /api/data/history/{ticker}`: Get historical data for a specific ticker.
- `GET /api/predict/{ticker}`: Get price predictions for a ticker.

### Smart Advisor
- `POST /api/advisor/recommendation`: Get AI-powered investment recommendations.
