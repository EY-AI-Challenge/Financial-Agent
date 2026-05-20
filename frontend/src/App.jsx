import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AssetDetails from './pages/AssetDetails'
import InvestmentSimulator from './pages/InvestmentSimulator'
import SmartAdvisor from './pages/SmartAdvisor'

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/assets/:ticker" element={<AssetDetails />} />
          <Route path="/simulator" element={<InvestmentSimulator />} />
          <Route path="/advisor" element={<SmartAdvisor />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
