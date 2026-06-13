import { NavLink, Outlet } from "react-router-dom";
import clsx from "clsx";

const NAV = [
  { to: "/", label: "Digest", icon: "✦" },
  { to: "/feed", label: "Topics", icon: "⊞" },
  { to: "/graph", label: "Graph", icon: "◎" },
  { to: "/sources", label: "Sources", icon: "⊕" },
];

export default function Layout() {
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
