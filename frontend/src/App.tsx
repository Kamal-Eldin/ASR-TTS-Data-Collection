
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Projects from './components/Projects';
import Recording from './components/Recording';
import Settings from './components/Settings';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 font-sans">
        <div className="max-w-6xl mx-auto">
          {/* Navigation Header */}
          <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-6xl mx-auto px-6 py-4">
              <div className="flex items-center justify-between">
                <Link to="/" className="text-2xl font-bold text-gray-900 hover:text-gray-700 transition">
                  Voice Dataset Collection
                </Link>
                <nav className="flex space-x-6">
                  <Link 
                    to="/" 
                    className="text-gray-600 hover:text-gray-900 font-medium transition"
                  >
                    Projects
                  </Link>
                  <Link 
                    to="/settings" 
                    className="text-gray-600 hover:text-gray-900 font-medium transition"
                  >
                    Settings
                  </Link>
                </nav>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="py-8">
            <Routes>
              <Route path="/" element={<Projects />} />
              <Route path="/recording/:projectId" element={<Recording />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
