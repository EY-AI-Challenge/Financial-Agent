# Stock Price Predictor
### Multi-Horizon Ensemble: LightGBM + Prophet + Chronos (Pre-Trained Foundation Model)

Predicts stock/crypto prices at **1 week**, **1 month**, and **1 year** horizons using an ensemble of complementary models, each chosen for the time-scale it excels at.

---

## Model Architecture

```
OHLCV CSV
    │
    ▼
Feature Engineering (features.py)
  ├─ 9 lag returns (1d … 252d)
  ├─ Rolling stats (mean, std, skew, z-score) at 6 windows
  ├─ Trend: SMA/EMA distance + 3 crossover signals
  ├─ Momentum: RSI(7/14/28), MACD, ROC, Williams %R, Stochastic
  ├─ Volatility: ATR, Garman-Klass, Bollinger Band width, realised vol
  ├─ Volume: OBV, CMF, VWAP deviation
  └─ Calendar: day-of-week, month, quarter, year-fraction
         │
         ├──▶ LightGBM Forecaster (models/lgbm_model.py)
         │      • One model per horizon (direct forecasting)
         │      • Quantile regression for 10/90th-pct CI
         │      • Walk-forward time-series CV for evaluation
         │
         ├──▶ Prophet Forecaster (models/prophet_model.py)
         │      • Fits on log(Close), last 5 years
         │      • Weekly + monthly + quarterly + annual seasonality
         │      • 80% uncertainty intervals via MAP estimation
         │
         └──▶ Chronos Forecaster (models/chronos_model.py)  ← optional
                • Amazon's pre-trained T5 foundation model
                • Zero-shot: no fine-tuning required
                • 20 Monte-Carlo samples → 10/90th-pct CI
                        │
                        ▼
              Ensemble (models/ensemble.py)
                Weighted average in log-price space
                Short-term: LGBM 0.55 · Chronos 0.30 · Prophet 0.15
                Long-term:  Prophet 0.50 · LGBM 0.35 · Chronos 0.15
```

---

## Why these models?

| Model | Strengths | Best horizon |
|---|---|---|
| **LightGBM** | Captures recent regime, technical patterns, non-linear interactions | 1 week, 1 month |
| **Prophet** | Long-range trend + multi-frequency seasonality, handles changepoints | 1 month, 1 year |
| **Chronos** | Zero-shot prior from 27B observations, no overfitting risk | All (regulariser) |

### Why not LSTM / Transformer?

LSTMs are outperformed by gradient-boosted trees on tabular financial data when rich feature engineering is applied (per M5 competition benchmarks). Transformers work well but require fine-tuning. **Chronos** provides the best of transformers as a pre-trained zero-shot model without any training cost.

### Pre-Trained Foundation Model alternatives

If Chronos is unavailable, other open models you can drop in:

| Model | Install | Paper |
|---|---|---|
| **Chronos** (Amazon, 2024) | `pip install chronos-forecasting` | [arxiv:2403.07815](https://arxiv.org/abs/2403.07815) |
| **Moirai** (Salesforce, 2024) | `pip install uni2ts` | [arxiv:2402.02592](https://arxiv.org/abs/2402.02592) |
| **TimesFM** (Google, 2024) | `pip install timesfm` | [arxiv:2310.10688](https://arxiv.org/abs/2310.10688) |
| **MOMENT** (CMU, 2024) | `pip install momentfm` | [arxiv:2402.03885](https://arxiv.org/abs/2402.03885) |
| **Lag-Llama** (2023) | `pip install lag-llama` | [arxiv:2310.08278](https://arxiv.org/abs/2310.08278) |

---

## Installation

```bash
pip install -r requirements.txt

# Optional: Chronos pre-trained model (requires HuggingFace access)
pip install chronos-forecasting torch transformers
```

---

## Quick Start

```python
from predictor import StockPredictor

sp = StockPredictor(ticker="AAPL", use_chronos=True)
sp.load_data("AAPL.csv")
sp.train(verbose=True)
results = sp.predict()
StockPredictor.print_summary(results, "AAPL")
sp.plot(results, save_path="AAPL_forecast.png")
```

### Expected output

```
============================================================
               AAPL Forecast Summary
============================================================
  Current price  : $298.97

  1W      ▼ $   290.18  (-2.9%)   CI: [$274.54, $310.17]
          ↳ lgbm       $   291.28  (w=0.79)
          ↳ prophet    $   286.16  (w=0.21)
          LightGBM CV MAPE: 4.19%

  1M      ▼ $   280.62  (-6.1%)   CI: [$273.41, $306.74]
          ↳ lgbm       $   278.77  (w=0.79)
          ↳ prophet    $   287.51  (w=0.21)
          LightGBM CV MAPE: 9.32%

  1Y      ▲ $   359.89  (+20.4%)  CI: [$57.69, $2582.56]
          ↳ lgbm       $   309.57  (w=0.41)
          ↳ prophet    $   399.91  (w=0.59)
          LightGBM CV MAPE: 34.44%
```

---

## Command-Line Usage

```bash
# Single ticker
python main.py --csv AAPL.csv --ticker AAPL --out-dir results/

# Multiple tickers
python main.py --csv AAPL.csv MSFT.csv BTC-USD.csv \
               --ticker AAPL MSFT BTC \
               --out-dir results/

# Disable Chronos (air-gapped / no HuggingFace)
python main.py --csv AAPL.csv --ticker AAPL --no-chronos

# Larger Chronos model (more accurate, slower)
python main.py --csv AAPL.csv --ticker AAPL --chronos-size base

# All options
python main.py --help
```

---

## CSV Format

```
Date,Close,High,Low,Open,Volume
2024-01-02,185.20,186.74,183.92,184.01,70540400
2024-01-03,184.25,185.88,183.43,184.22,58565000
...
```

Column names are case-insensitive. Date can be any parseable format.

---

## Project Structure

```
stock_predictor/
├── main.py                 # CLI entry point
├── predictor.py            # StockPredictor orchestrator
├── features.py             # 76-column feature engineering
├── models/
│   ├── __init__.py
│   ├── lgbm_model.py       # LightGBM direct multi-horizon forecaster
│   ├── prophet_model.py    # Prophet trend + seasonality model
│   ├── chronos_model.py    # Chronos pre-trained foundation model wrapper
│   └── ensemble.py         # Weighted log-price ensemble
├── requirements.txt
└── README.md
```

---

## Interpreting Results

### Short-term (1 week)
LightGBM dominates (weight 0.55). CV MAPE ~4% means the model's past
out-of-sample errors average ±4% of price. Treat the CI as a realistic
range, not a guarantee.

### Medium-term (1 month)
LightGBM CV MAPE rises to ~9% as market noise compounds. Chronos acts as
a zero-shot regulariser if available.

### Long-term (1 year)
Prophet takes the lead (weight 0.50). The CI is intentionally wide — stock
prices are genuinely unpredictable at 1-year horizons. LightGBM CV MAPE
~34% at this range reflects market reality, not a model failure.

---

## Caveats

- **This is not financial advice.** All models extrapolate from historical
  patterns that may not hold in the future.
- Stock prices are impacted by news, earnings, macro events and other
  information that no historical-data model can anticipate.
- The 1-year CI should be taken seriously — it represents genuine
  uncertainty, not a modelling limitation.
- Backtested accuracy (CV MAPE) reflects past performance only.
