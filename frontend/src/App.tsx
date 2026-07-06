import { Link, Route, Routes } from "react-router-dom";

import { DashboardPage } from "./pages/DashboardPage";
import { NewProjectPage } from "./pages/NewProjectPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

const navItems = [
  ["Dashboard", "/"],
  ["New project", "/new-project"],
] as const;

export function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-white/10 bg-slate-950/90">
        <nav
          aria-label="Primary navigation"
          className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6"
        >
          <Link className="font-semibold tracking-tight" to="/">
            FreelanceShield AI
          </Link>
          <div className="flex gap-4 text-sm text-slate-300">
            {navItems.map(([label, path]) => (
              <Link className="hover:text-white" key={path} to={path}>
                {label}
              </Link>
            ))}
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <Routes>
          <Route element={<DashboardPage />} path="/" />
          <Route element={<NewProjectPage />} path="/new-project" />
          <Route
            element={<PlaceholderPage title="Agreement" />}
            path="/agreement/:projectId"
          />
          <Route
            element={<PlaceholderPage title="Evidence timeline" />}
            path="/timeline/:projectId"
          />
          <Route
            element={<PlaceholderPage title="Follow-up" />}
            path="/follow-up/:projectId"
          />
        </Routes>
      </main>
    </div>
  );
}
