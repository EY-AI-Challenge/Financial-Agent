import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const auth = {
  register: (email, password) =>
    apiClient.post('/auth/register', { email, password }),
  login: (email, password) =>
    apiClient.post('/auth/login', { email, password }),
}

export const data = {
  getHistory: (ticker) =>
    apiClient.get(`/data/history/${ticker}`),
  getTickers: () =>
    apiClient.get('/data/tickers'),
}

export const predictions = {
  getTickerPredictions: (ticker) =>
    apiClient.get(`/predict/${ticker}`),
  getPortfolioPredictions: (portfolio) =>
    apiClient.post('/predict/portfolio', portfolio),
}

export const advisor = {
  getRecommendations: (portfolio) =>
    apiClient.post('/advisor/recommendation', portfolio),
  getRiskAssessment: (portfolio) =>
    apiClient.post('/advisor/risk-assessment', portfolio),
}

export default apiClient
