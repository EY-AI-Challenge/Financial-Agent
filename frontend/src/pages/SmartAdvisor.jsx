import { useState } from 'react'
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'

function SmartAdvisor() {
  const [riskTolerance, setRiskTolerance] = useState('medium')

  const recommendations = [
    {
      id: 1,
      ticker: 'AAPL',
      action: 'BUY',
      confidence: 87,
      reason: 'Strong uptrend detected. 1-month prediction: +6.8%',
      icon: TrendingUp,
      color: 'accent-green'
    },
    {
      id: 2,
      ticker: 'GOOGL',
      action: 'SELL',
      confidence: 78,
      reason: 'Potential downward trend. Consider taking profits.',
      icon: TrendingDown,
      color: 'accent-red'
    },
    {
      id: 3,
      ticker: 'MSFT',
      action: 'HOLD',
      confidence: 92,
      reason: 'Stable position. Monitor for entry opportunities.',
      icon: AlertCircle,
      color: 'accent-blue'
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Smart Advisor</h1>
        <p className="text-gray-400">AI-powered recommendations based on ML predictions</p>
      </div>

      {/* Risk Profile */}
      <div className="glass-effect p-6 rounded-xl">
        <label className="block text-sm font-medium text-gray-300 mb-4">Risk Tolerance</label>
        <div className="grid grid-cols-3 gap-4">
          {['low', 'medium', 'high'].map((level) => (
            <button
              key={level}
              onClick={() => setRiskTolerance(level)}
              className={`py-3 px-4 rounded-lg font-medium transition-all ${
                riskTolerance === level
                  ? 'bg-accent-blue text-white'
                  : 'bg-dark-700 text-gray-300 hover:bg-dark-800'
              }`}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-white">Your Recommendations</h2>
        
        {recommendations.map((rec) => {
          const Icon = rec.icon
          return (
            <div key={rec.id} className="glass-effect p-6 rounded-xl hover:bg-white/15 transition-all">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg bg-${rec.color}/20`}>
                    <Icon className={`text-${rec.color}`} size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">{rec.ticker}</h3>
                    <p className="text-sm text-gray-400">{rec.reason}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-lg font-bold text-${rec.color}`}>{rec.action}</p>
                  <p className="text-sm text-gray-400">{rec.confidence}% confidence</p>
                </div>
              </div>

              {/* Confidence Meter */}
              <div className="w-full bg-dark-700 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full bg-${rec.color}`}
                  style={{ width: `${rec.confidence}%` }}
                ></div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Portfolio Health */}
      <div className="glass-effect p-6 rounded-xl">
        <h2 className="text-xl font-bold text-white mb-4">Portfolio Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Diversification</p>
            <p className="text-2xl font-bold text-accent-green">85%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Risk Score</p>
            <p className="text-2xl font-bold text-accent-blue">42%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Expected Return</p>
            <p className="text-2xl font-bold text-accent-green">+12.5%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Health Score</p>
            <p className="text-2xl font-bold text-accent-green">88%</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SmartAdvisor
