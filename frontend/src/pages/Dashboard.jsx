import { useEffect, useState } from 'react'
import { data, portfolio as portfolioApi } from '../services/api'
import {
  buildDistributionGradient,
  buildPortfolioSummary,
  getDemoPortfolio,
} from '../utils/portfolio'

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value || 0)
}

function formatSignedCurrency(value) {
  const formatted = formatCurrency(Math.abs(value))
  return value >= 0 ? `+${formatted}` : `-${formatted}`
}

async function fetchLatestPriceInfo(ticker) {
  try {
    const response = await data.getHistory(ticker)
    const history = Array.isArray(response.data) ? response.data : []

    if (history.length === 0) {
      return { currentPrice: null, previousClose: null }
    }

    const sortedHistory = [...history].sort((left, right) => {
      const leftDate = new Date(left.date || left.Date || 0).getTime()
      const rightDate = new Date(right.date || right.Date || 0).getTime()
      return leftDate - rightDate
    })

    const latest = sortedHistory[sortedHistory.length - 1]
    const previous = sortedHistory[sortedHistory.length - 2] || latest

    return {
      currentPrice: Number(latest.close ?? latest.Close ?? latest.adj_close ?? latest.AdjClose ?? latest.Adj_Close ?? latest.price ?? 0),
      previousClose: Number(previous.close ?? previous.Close ?? previous.adj_close ?? previous.AdjClose ?? previous.Adj_Close ?? previous.price ?? 0),
    }
  } catch (error) {
    return { currentPrice: null, previousClose: null }
  }
}

function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [sourceLabel, setSourceLabel] = useState('Demo portfolio')

  useEffect(() => {
    let isMounted = true

    async function loadPortfolio() {
      setIsLoading(true)
      setError('')

      try {
        let transactions = []
        let label = 'Demo portfolio'

        try {
          const response = await portfolioApi.getCurrentPortfolio()
          transactions = Array.isArray(response.data) ? response.data : []
          label = 'Live portfolio'
        } catch (portfolioError) {
          transactions = getDemoPortfolio()
          label = 'Demo portfolio'
        }

        if (!transactions.length) {
          transactions = getDemoPortfolio()
          label = 'Demo portfolio'
        }

        const uniqueTickers = [...new Set(transactions.map((entry) => entry.ticker_symbol).filter(Boolean))]
        const priceEntries = await Promise.all(
          uniqueTickers.map(async (ticker) => {
            const priceInfo = await fetchLatestPriceInfo(ticker)
            return [ticker, priceInfo]
          }),
        )

        const priceMap = Object.fromEntries(priceEntries)
        const portfolioSummary = buildPortfolioSummary(transactions, priceMap)

        if (isMounted) {
          setSummary(portfolioSummary)
          setSourceLabel(label)
        }
      } catch (loadError) {
        if (isMounted) {
          setError('Unable to load portfolio data right now.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadPortfolio()

    return () => {
      isMounted = false
    }
  }, [])

  const distributionGradient = summary ? buildDistributionGradient(summary.distribution) : 'conic-gradient(#334155 0deg 360deg)'
  const topHolding = summary?.holdings?.[0]
  const recommendationsCount = Math.max(summary?.holdings?.length || 0, 1)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">
            {isLoading ? 'Loading portfolio metrics...' : `Portfolio analytics powered by ${sourceLabel.toLowerCase()}`}
          </p>
        </div>

        {summary && (
          <div className="glass-effect px-4 py-3 rounded-xl text-sm text-gray-600 dark:text-gray-300">
            <span className="font-semibold text-gray-900 dark:text-white">Top holding:</span>{' '}
            {topHolding?.ticker} {topHolding ? `(${topHolding.weight.toFixed(1)}%)` : ''}
          </div>
        )}
      </div>

      {error && (
        <div className="glass-effect border border-accent-red/30 px-4 py-3 rounded-xl text-accent-red">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">Total Portfolio Value</p>
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
            {isLoading ? '—' : formatCurrency(summary?.totalValue)}
          </h3>
          <p className={`text-sm ${summary && summary.totalGainLoss >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
            {isLoading ? 'Calculating...' : `${formatSignedCurrency(summary?.totalGainLoss || 0)} total P&L`}
          </p>
        </div>

        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">24h Change</p>
          <h3 className={`text-3xl font-bold mb-1 ${summary && summary.dailyChange >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
            {isLoading ? '—' : formatSignedCurrency(summary?.dailyChange || 0)}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            {isLoading ? 'Calculating...' : `${(summary?.dailyChangePercent || 0).toFixed(2)}% from previous close`}
          </p>
        </div>

        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">AI Recommendations</p>
          <h3 className="text-3xl font-bold text-accent-blue mb-1">{isLoading ? '—' : recommendationsCount}</h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            {isLoading ? 'Analyzing...' : 'Opportunities inferred from current holdings'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-6">
        <div className="glass-effect p-6 rounded-xl space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Portfolio Distribution</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Position weights across the current portfolio</p>
            </div>
            {summary && (
              <div className="text-right">
                <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Invested</p>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">{formatCurrency(summary.totalInvested)}</p>
              </div>
            )}
          </div>

          <div className="grid gap-6 xl:grid-cols-[260px_1fr] items-center">
            <div className="mx-auto flex h-52 w-52 items-center justify-center rounded-full border border-gray-200 dark:border-white/10 p-4">
              <div
                className="h-full w-full rounded-full shadow-inner"
                style={{ background: distributionGradient }}
                aria-label="Portfolio distribution chart"
              />
            </div>

            <div className="space-y-3">
              {summary?.distribution?.length ? (
                summary.distribution.map((entry) => (
                  <div key={entry.ticker} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-gray-800 dark:text-gray-200">
                        <span className="h-3 w-3 rounded-full" style={{ backgroundColor: entry.color }} />
                        {entry.ticker}
                      </span>
                      <span className="text-gray-600 dark:text-gray-400">{entry.weight.toFixed(1)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-gray-200 dark:bg-dark-700 overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${entry.weight}%`, backgroundColor: entry.color }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400">No positions available yet.</div>
              )}
            </div>
          </div>
        </div>

        <div className="glass-effect p-6 rounded-xl space-y-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Performance Snapshot</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Gains, losses and exposure by asset</p>
          </div>

          <div className="space-y-3">
            {summary?.holdings?.length ? (
              summary.holdings.map((holding) => (
                <div key={holding.ticker} className="rounded-xl bg-gray-100 dark:bg-dark-700/70 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{holding.ticker}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {holding.netQuantity.toFixed(4)} units · Avg {formatCurrency(holding.avgBuyPrice)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900 dark:text-white">{formatCurrency(holding.marketValue)}</p>
                      <p className={`text-xs ${holding.gainLoss >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {formatSignedCurrency(holding.gainLoss)} · {holding.gainLossPercent.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-gray-500 dark:text-gray-400">Portfolio is empty.</div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-effect p-6 rounded-xl">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Market Insights</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">S&P 500</span>
              <span className="text-accent-green">+2.1%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Bitcoin</span>
              <span className="text-accent-green">+3.5%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Tech Sector</span>
              <span className="text-accent-red">-1.2%</span>
            </div>
          </div>
        </div>

        <div className="glass-effect p-6 rounded-xl">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Smart Advisor</h2>
          <div className="space-y-3">
            <div className="bg-gray-100 dark:bg-dark-700 p-3 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300">Portfolio concentrated in {topHolding?.ticker || 'multiple assets'}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Largest allocation: {topHolding ? `${topHolding.weight.toFixed(1)}%` : '0%'}</p>
            </div>
            <div className="bg-gray-100 dark:bg-dark-700 p-3 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300">Estimated gain/loss tracked from cost basis</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                {isLoading ? 'Calculating...' : `${formatSignedCurrency(summary?.totalGainLoss || 0)} overall`}
              </p>
            </div>
            <div className="bg-gray-100 dark:bg-dark-700 p-3 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300">Distribution chart updates with holdings</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Reflects current portfolio weights</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
