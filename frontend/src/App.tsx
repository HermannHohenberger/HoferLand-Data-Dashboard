import { Dashboard } from './pages/Dashboard'
import { Impressum } from './pages/Impressum'
import { Maintenance } from './pages/Maintenance'
import { Ueber } from './pages/Ueber'

function App() {
  const path = window.location.pathname.replace(/\/+$/, '') || '/'
  if (path === '/ueber') {
    return <Ueber />
  }
  if (path === '/impressum') {
    return <Impressum />
  }
  if (path === '/maintenance') {
    return <Maintenance />
  }
  return <Dashboard />
}

export default App
