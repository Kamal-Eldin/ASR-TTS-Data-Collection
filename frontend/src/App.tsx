import { Routes, Route, Navigate, Link, Outlet, useNavigate } from "react-router-dom";

import Projects from "./components/Projects";
import Recording from "./components/Recording";
import Settings from "./components/Settings";
import SignIn from "./Auth/SignIn";

function AppLayout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/signin", { replace: true });
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <div className="max-w-6xl mx-auto">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Link
                to="/projects"
                className="text-2xl font-bold text-gray-900 hover:text-gray-700 transition"
              >
                Voice Dataset Collection
              </Link>

              <nav className="flex space-x-6 items-center">
                <Link
                  to="/projects"
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

                <button
                  onClick={handleLogout}
                  className="text-red-600 rounded-lg px-4 py-2 font-semibold hover:bg-red-200 transition"
                >
                  Logout
                </button>
              </nav>
            </div>
          </div>
        </header>

        <main className="py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      {/* open signin first */}
      <Route path="/" element={<Navigate to="/signin" replace />} />

      {/* auth page */}
      <Route
        path="/signin"
        element={
          localStorage.getItem("token")
            ? <Navigate to="/projects" replace />
            : <SignIn />
        }
      />

      {/* main app pages */}
      <Route element={<AppLayout />}>
        <Route path="/projects" element={<Projects />} />
        <Route path="/recording/:projectId" element={<Recording />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      {/* fallback */}
      <Route path="*" element={<Navigate to="/signin" replace />} />
    </Routes>
  );
}
