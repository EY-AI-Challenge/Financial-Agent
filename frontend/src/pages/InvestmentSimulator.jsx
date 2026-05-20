import { useState } from 'react'

function InvestmentSimulator() {
  const [initialInvestment, setInitialInvestment] = useState(10000)
  const [selectedAssets, setSelectedAssets] = useState(['AAPL', 'GOOGL'])
  const [timeHorizon, setTimeHorizon] = useState('1y')

  const assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'BTC-USD', 'ETH-USD']
  const projectedValue = initialInvestment * 1.25

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Investment Simulator</h1>
        <p className="text-gray-400">Test your investment strategies with historical trends</p>
      </div>

      {/* Configuration */}
      <div className="glass-effect p-6 rounded-xl space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Initial Investment</label>
          <input
            type="number"
            value={initialInvestment}
            onChange={(e) => setInitialInvestment(Number(e.target.value))}
            className="w-full bg-dark-700 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-accent-blue"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Time Horizon</label>
          <select
            value={timeHorizon}
            onChange={(e) => setTimeHorizon(e.target.value)}
            className="w-full bg-dark-700 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-accent-blue"
          >
            <option value="1w">1 Week</option>
            <option value="1m">1 Month</option>
            <option value="1y">1 Year</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Select Assets</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {assets.map((asset) => (
              <label key={asset} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedAssets.includes(asset)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedAssets([...selectedAssets, asset])
                    } else {
                      setSelectedAssets(selectedAssets.filter(a => a !== asset))
                    }
                  }}
                  className="w-4 h-4 rounded"
                />
                <span className="text-sm text-gray-300">{asset}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">Initial Investment</p>
          <p className="text-3xl font-bold text-white">${initialInvestment.toLocaleString()}</p>
        </div>
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">Projected Value ({timeHorizon})</p>
          <p className="text-3xl font-bold text-accent-green">${projectedValue.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
          <p className="text-xs text-gray-500 mt-2">+25% projected gain</p>
        </div>
      </div>

      {/* Portfolio Allocation */}
      <div className="glass-effect p-6 rounded-xl">
        <h2 className="text-xl font-bold text-white mb-4">Suggested Allocation</h2>
        <div className="space-y-3">
          {selectedAssets.map((asset) => (
            <div key={asset} className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="text-gray-400">{asset}</span>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-32 h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent-blue"
                    style={{ width: `${(100 / selectedAssets.length)}%` }}
                  ></div>
                </div>
                <span className="text-white font-medium w-12">{(100 / selectedAssets.length).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default InvestmentSimulator
