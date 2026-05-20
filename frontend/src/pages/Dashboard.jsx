function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-gray-400">Welcome to your financial decision support platform</p>
      </div>

      {/* Portfolio Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Portfolio Value */}
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">Total Portfolio Value</p>
          <h3 className="text-3xl font-bold text-white mb-1">$124,589.50</h3>
          <p className="text-accent-green text-sm">+5.2% today</p>
        </div>

        {/* 24h Change */}
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">24h Change</p>
          <h3 className="text-3xl font-bold text-accent-green">+$6,450.25</h3>
          <p className="text-gray-400 text-sm">+5.2% gain</p>
        </div>

        {/* Recommended Actions */}
        <div className="glass-effect p-6 rounded-xl">
          <p className="text-gray-400 text-sm mb-2">AI Recommendations</p>
          <h3 className="text-3xl font-bold text-accent-blue">3</h3>
          <p className="text-gray-400 text-sm">New opportunities detected</p>
        </div>
      </div>

      {/* Market Insights & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Market Insights */}
        <div className="glass-effect p-6 rounded-xl">
          <h2 className="text-xl font-bold text-white mb-4">Market Insights</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">S&P 500</span>
              <span className="text-accent-green">+2.1%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Bitcoin</span>
              <span className="text-accent-green">+3.5%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Tech Sector</span>
              <span className="text-accent-red">-1.2%</span>
            </div>
          </div>
        </div>

        {/* Top Recommendations */}
        <div className="glass-effect p-6 rounded-xl">
          <h2 className="text-xl font-bold text-white mb-4">Smart Advisor</h2>
          <div className="space-y-3">
            <div className="bg-dark-700 p-3 rounded-lg">
              <p className="text-sm text-gray-400">Buy signal detected for AAPL</p>
              <p className="text-xs text-gray-500 mt-1">Confidence: 87%</p>
            </div>
            <div className="bg-dark-700 p-3 rounded-lg">
              <p className="text-sm text-gray-400">Hold position on MSFT</p>
              <p className="text-xs text-gray-500 mt-1">Confidence: 92%</p>
            </div>
            <div className="bg-dark-700 p-3 rounded-lg">
              <p className="text-sm text-gray-400">Sell signal for GOOGL</p>
              <p className="text-xs text-gray-500 mt-1">Confidence: 78%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
