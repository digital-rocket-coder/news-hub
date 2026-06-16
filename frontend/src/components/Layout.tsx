import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { pollAllSources } from "../api/client";

const NAV = [
  { to: "/", label: "Digest", icon: "✦" },
  { to: "/feed", label: "Topics", icon: "⊞" },
  { to: "/graph", label: "Graph", icon: "◎" },
  { to: "/sources", label: "Sources", icon: "⊕" },
];

export default function Layout() {
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const qc = useQueryClient();

  async function handleRefresh() {
    setLoading(true);
    setDone(false);
    try {
      await pollAllSources();
      // Give sources ~8s to fetch, then invalidate all queries
      setTimeout(() => {
        qc.invalidateQueries();
        setLoading(false);
        setDone(true);
        setTimeout(() => setDone(false), 3000);
      }, 8000);
    } catch {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-[#111120] border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-6">
          <span className="text-lg font-bold tracking-tight text-white">
            news<span className="text-accent">hub</span>
          </span>
          <p className="text-xs text-gray-500 mt-0.5">your second brain</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 space-y-1">
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent/10 text-accent"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                )
              }
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Refresh button */}
        <div className="px-3 pb-4">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className={clsx(
              "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              done
                ? "bg-green-500/10 text-green-400"
                : loading
                ? "bg-gray-800/50 text-gray-500 cursor-not-allowed"
                : "bg-accent/10 text-accent hover:bg-accent/20"
            )}
          >
            <span
              className={clsx("text-base leading-none", loading && "animate-spin")}
            >
              {done ? "✓" : "↻"}
            </span>
            {done ? "Updated!" : loading ? "Fetching…" : "Refresh"}
          </button>
        </div>

        {/* Footer */}
        <div className="px-5 pb-5">
          <p className="text-xs text-gray-600">Pull, not push.</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
