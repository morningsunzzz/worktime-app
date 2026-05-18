import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ClockPage from './pages/ClockPage'
import HistoryPage from './pages/HistoryPage'
import StatsPage from './pages/StatsPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ClockPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Layout>
  )
}
