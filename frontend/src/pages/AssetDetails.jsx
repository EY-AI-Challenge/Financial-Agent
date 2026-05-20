import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { data as apiData } from '../services/api'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'

function AssetDetails() {
  const { ticker } = useParams()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!ticker) return
    setLoading(true)
    setError(null)
    apiData
      .getHistory(ticker)
      .then((res) => {
        // Expecting array of records with at least 'Date' and 'Close' columns
        const parsed = (res.data || []).map((r) => ({
          date: r.Date || r.date || r.datetime || r.Timestamp || r.timestamp,
          close: r.Close !== undefined ? Number(r.Close) : Number(r.close || 0),
        }))
        // Sort by date ascending (assumes ISO-like dates)
        parsed.sort((a, b) => (a.date > b.date ? 1 : a.date < b.date ? -1 : 0))
        setHistory(parsed)
      })
      .catch((err) => {
        console.error('Failed to load history', err)
        setError('Failed to load history')
      })
      .finally(() => setLoading(false))
  }, [ticker])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">{ticker || 'Asset'} Details</h1>
        <p className="text-gray-400">Historical data and price predictions</p>
      </div>

      {/* Price Info */}
      <div className="glass-effect p-6 rounded-xl">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm mb-1">Current Price</p>
            <p className="text-2xl font-bold text-white">
              {history.length ? `$${history[history.length - 1].close.toFixed(2)}` : '—'}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">24h Change</p>
            <p className="text-2xl font-bold text-accent-green">{/* compute if available */}—</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">52-Week High</p>
            <p className="text-2xl font-bold text-white">—</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">52-Week Low</p>
            <p className="text-2xl font-bold text-white">—</p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="glass-effect p-6 rounded-xl h-96">
        <h2 className="text-xl font-bold text-white mb-4">Price History Chart</h2>
        <div className="h-80 rounded-lg">
          {loading && (
            <div className="h-full flex items-center justify-center text-gray-400">Loading chart…</div>
          )}
          {error && (
            <div className="h-full flex items-center justify-center text-red-400">{error}</div>
          )}
          {!loading && !error && history.length > 0 && (
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={history} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fill: '#cbd5e1' }} />
                <YAxis tick={{ fill: '#cbd5e1' }} domain={["dataMin", "dataMax"]} />
                <Tooltip />
                <Line type="monotone" dataKey="close" stroke="#60a5fa" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
          {!loading && !error && history.length === 0 && (
            <div className="h-full flex items-center justify-center text-gray-400">No historical data available.</div>
          )}
        </div>
      </div>

      {/* Predictions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">1-Week Prediction</p>
          <p className="text-2xl font-bold text-accent-green">$145.80</p>
          <p className="text-xs text-gray-500 mt-2">+2.3% expected</p>
        </div>
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">1-Month Prediction</p>
          <p className="text-2xl font-bold text-accent-green">$152.30</p>
          <p className="text-xs text-gray-500 mt-2">+6.8% expected</p>
        </div>
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">1-Year Prediction</p>
          <p className="text-2xl font-bold text-accent-blue">$178.50</p>
          <p className="text-xs text-gray-500 mt-2">+25.2% expected</p>
        </div>
      </div>
    </div>
  )
}

export default AssetDetails
