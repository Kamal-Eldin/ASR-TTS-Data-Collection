import { Routes, Route, Navigate, Link, Outlet, useNavigate } from "react-router-dom";

import Projects from "./components/Projects";
import Recording from "./components/Recording";
import Settings from "./components/Settings";
import Profile from "./components/Profile";
import SignIn from "./Auth/SignIn";
import ForgotPassword from "./Auth/ForgotPassword";
import ResetPassword from "./Auth/ResetPassword";
import { clearStoredAuth, getStoredUser, isAuthenticated } from "./utils/auth";

function RequireAuth() {
  return isAuthenticated() ? <Outlet /> : <Navigate to="/signin" replace />;
}

function AppLayout() {
  const navigate = useNavigate();
  const storedUser = getStoredUser();
  const profileInitial = (storedUser?.firstName?.[0] || storedUser?.email?.[0] || "U").toUpperCase();

  const handleLogout = () => {
    clearStoredAuth();
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
                Voice Force
              </Link>

              <nav className="flex items-center gap-6">
                <Link
                  to="/profile"
                  className="flex items-center gap-3 text-gray-600 hover:text-gray-900 font-medium transition"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-sm font-semibold text-white">
                    {profileInitial}
                  </span>
                  <span>Profile</span>
                </Link>
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
      <Route
        path="/"
        element={<Navigate to={isAuthenticated() ? "/projects" : "/signin"} replace />}
      />

      <Route
        path="/signin"
        element={isAuthenticated() ? <Navigate to="/projects" replace /> : <SignIn />}
      />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/profile" element={<Profile />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/recording/:projectId" element={<Recording />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>

      <Route
        path="*"
        element={<Navigate to={isAuthenticated() ? "/projects" : "/signin"} replace />}
      />
    </Routes>
  );
}
