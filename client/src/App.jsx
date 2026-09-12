import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import Home from './pages/Home'

function App() {
  return (
    <Router>
      <header className="border-b border-gray-200 p-4">
        <h1 className="text-2xl font-bold">FurtherXpert</h1>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </Router>
  )
}

export default App
