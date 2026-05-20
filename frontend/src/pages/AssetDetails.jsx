import { useParams } from 'react-router-dom'

function AssetDetails() {
  const { ticker } = useParams()

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
            <p className="text-2xl font-bold text-white">$142.50</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">24h Change</p>
            <p className="text-2xl font-bold text-accent-green">+2.3%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">52-Week High</p>
            <p className="text-2xl font-bold text-white">$165.20</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-1">52-Week Low</p>
            <p className="text-2xl font-bold text-white">$120.30</p>
          </div>
        </div>
      </div>

      {/* Charts Placeholder */}
      <div className="glass-effect p-6 rounded-xl h-96">
        <h2 className="text-xl font-bold text-white mb-4">Price History Chart</h2>
        <div className="h-80 bg-dark-700 rounded-lg flex items-center justify-center text-gray-400">
          Chart will be rendered here
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
