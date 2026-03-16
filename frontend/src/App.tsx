import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";

import Dashboard from "./pages/Dashboard";
import Scanner from "./pages/Scanner";
import Password from "./pages/Password";
import About from "./pages/About";

import { AdminLogin, AdminDashboard } from "./admin";

export default function App() {
  return (
    <Routes>
      {/* Admin Routes (no sidebar layout) */}
      <Route path="/admin" element={<AdminLogin />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />

      {/* Main App Routes */}
      <Route
        path="*"
        element={
          <div className="flex min-h-screen" style={{ background: "var(--bg-deep)" }}>
            <Sidebar />
            <main
              className="flex-1 overflow-y-auto min-h-screen bg-grid"
              style={{
                background: `
                  radial-gradient(ellipse 80% 50% at 50% -20%, rgba(6,182,212,0.05) 0%, transparent 70%),
                  var(--bg-deep)
                `,
                padding: "32px 44px",
              }}
            >
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/scanner" element={<Scanner />} />
                <Route path="/password" element={<Password />} />
                <Route path="/about" element={<About />} />
              </Routes>
            </main>
          </div>
        }
      />
    </Routes>
  );
}
