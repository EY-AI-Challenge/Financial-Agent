export const DEMO_PORTFOLIO = [
  {
    ticker_symbol: 'AAPL',
    transaction_type: 'BUY',
    quantity: 25,
    price_per_unit: 182.4,
  },
  {
    ticker_symbol: 'MSFT',
    transaction_type: 'BUY',
    quantity: 18,
    price_per_unit: 410.15,
  },
  {
    ticker_symbol: 'GOOGL',
    transaction_type: 'BUY',
    quantity: 12,
    price_per_unit: 148.9,
  },
  {
    ticker_symbol: 'BTC-USD',
    transaction_type: 'BUY',
    quantity: 0.45,
    price_per_unit: 61250,
  },
]

const DEFAULT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export function getDemoPortfolio() {
  return DEMO_PORTFOLIO.map((transaction) => ({ ...transaction }))
}

export function normalizePortfolioTransactions(transactions) {
  const buckets = new Map()

  transactions.forEach((transaction) => {
    const ticker = transaction.ticker_symbol
    if (!ticker) {
      return
    }

    const quantity = Number(transaction.quantity || 0)
    const pricePerUnit = Number(transaction.price_per_unit || 0)
    const transactionType = String(transaction.transaction_type || 'BUY').toUpperCase()

    if (!buckets.has(ticker)) {
      buckets.set(ticker, {
        ticker,
        buyQuantity: 0,
        buyCost: 0,
        sellQuantity: 0,
      })
    }

    const entry = buckets.get(ticker)

    if (transactionType === 'SELL') {
      entry.sellQuantity += quantity
    } else {
      entry.buyQuantity += quantity
      entry.buyCost += quantity * pricePerUnit
    }
  })

  return Array.from(buckets.values())
    .map((entry) => {
      const netQuantity = Math.max(entry.buyQuantity - entry.sellQuantity, 0)
      const avgBuyPrice = entry.buyQuantity > 0 ? entry.buyCost / entry.buyQuantity : 0

      return {
        ticker: entry.ticker,
        netQuantity,
        avgBuyPrice,
      }
    })
    .filter((entry) => entry.netQuantity > 0)
}

export function buildPortfolioSummary(transactions, priceMap = {}) {
  const holdings = normalizePortfolioTransactions(transactions)

  const enrichedHoldings = holdings.map((holding) => {
    const priceInfo = priceMap[holding.ticker] || {}
    const currentPrice = Number(priceInfo.currentPrice ?? holding.avgBuyPrice)
    const previousClose = Number(priceInfo.previousClose ?? currentPrice)
    const marketValue = holding.netQuantity * currentPrice
    const previousValue = holding.netQuantity * previousClose
    const investedValue = holding.netQuantity * holding.avgBuyPrice
    const gainLoss = marketValue - investedValue
    const gainLossPercent = investedValue > 0 ? (gainLoss / investedValue) * 100 : 0
    const dailyChange = marketValue - previousValue

    return {
      ...holding,
      currentPrice,
      previousClose,
      marketValue,
      investedValue,
      gainLoss,
      gainLossPercent,
      dailyChange,
    }
  })

  const totalValue = enrichedHoldings.reduce((sum, holding) => sum + holding.marketValue, 0)
  const totalInvested = enrichedHoldings.reduce((sum, holding) => sum + holding.investedValue, 0)
  const totalGainLoss = totalValue - totalInvested
  const totalGainLossPercent = totalInvested > 0 ? (totalGainLoss / totalInvested) * 100 : 0
  const dailyChange = enrichedHoldings.reduce((sum, holding) => sum + holding.dailyChange, 0)
  const dailyChangePercent = totalInvested > 0 ? (dailyChange / totalInvested) * 100 : 0

  const distribution = totalValue > 0
    ? enrichedHoldings
        .map((holding, index) => ({
          ...holding,
          weight: (holding.marketValue / totalValue) * 100,
          color: DEFAULT_COLORS[index % DEFAULT_COLORS.length],
        }))
        .sort((left, right) => right.marketValue - left.marketValue)
    : []

  return {
    totalValue,
    totalInvested,
    totalGainLoss,
    totalGainLossPercent,
    dailyChange,
    dailyChangePercent,
    holdings: enrichedHoldings.sort((left, right) => right.marketValue - left.marketValue),
    distribution,
  }
}

export function buildDistributionGradient(distribution) {
  if (!distribution.length) {
    return 'conic-gradient(#334155 0deg 360deg)'
  }

  let accumulated = 0
  const segments = distribution.map((entry) => {
    const start = accumulated
    accumulated += entry.weight
    return `${entry.color} ${start.toFixed(2)}% ${accumulated.toFixed(2)}%`
  })

  return `conic-gradient(${segments.join(', ')})`
}
