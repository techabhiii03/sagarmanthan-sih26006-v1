import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Compass,
  Ship,
  Anchor,
  TrendingUp,
  AlertTriangle,
  Map,
  FileText,
  Settings2,
  Waves,
  Menu,
  X,
  Clock,
} from 'lucide-react'
import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import DecisionCenter from './pages/DecisionCenter'
import ForecastPage from './pages/ForecastPage'
import VesselPage from './pages/VesselPage'
import PortPage from './pages/PortPage'
import ContractPage from './pages/ContractPage'
import RiskPage from './pages/RiskPage'
import MapPage from './pages/MapPage'
import ScenarioPage from './pages/ScenarioPage'
import TransparencyPage from './pages/TransparencyPage'
import IdlePage from './pages/IdlePage'
import { DecisionProvider } from './hooks/useDecision'

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/decision', label: 'Decision Center', icon: Compass },
  { to: '/forecast', label: 'Freight Forecast', icon: TrendingUp },
  { to: '/vessel', label: 'Vessel Optimizer', icon: Ship },
  { to: '/ports', label: 'Port Intelligence', icon: Anchor },
  { to: '/contract', label: 'Contract Optimizer', icon: FileText },
  { to: '/idle', label: 'Idle & Positioning', icon: Clock },
  { to: '/risk', label: 'Risk Center', icon: AlertTriangle },
  { to: '/scenario', label: 'Scenario Analysis', icon: Settings2 },
  { to: '/map', label: 'Maritime Map', icon: Map },
  { to: '/transparency', label: 'Data & Models', icon: Waves },
]

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={onClose} />
      )}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-navy-900 border-r border-navy-700/60 transform transition-transform duration-200 lg:translate-x-0 lg:static lg:z-auto ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-5 py-5 border-b border-navy-700/50">
          <div className="w-9 h-9 rounded-lg bg-ocean-500/20 flex items-center justify-center">
            <Waves className="w-5 h-5 text-ocean-400" />
          </div>
          <div>
            <div className="font-bold text-white tracking-tight">SagarManthan</div>
            <div className="text-[10px] text-navy-400 uppercase tracking-wider">SIH26006 · SAIL</div>
          </div>
          <button className="ml-auto lg:hidden text-navy-400" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <nav className="p-3 space-y-0.5 overflow-y-auto max-h-[calc(100vh-80px)]">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-ocean-500/15 text-ocean-400 border border-ocean-500/20'
                    : 'text-navy-300 hover:bg-navy-800 hover:text-navy-100'
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-navy-700/50 text-[10px] text-navy-500">
          Demonstration Prototype · SIH 2026
        </div>
      </aside>
    </>
  )
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <DecisionProvider>
      <div className="flex min-h-screen">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="sticky top-0 z-30 bg-navy-950/90 backdrop-blur border-b border-navy-800 px-4 py-3 flex items-center gap-3">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-navy-800 text-navy-300"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={20} />
            </button>
            <div className="text-sm text-navy-400">
              {nav.find((n) => n.to === location.pathname)?.label || 'SagarManthan'}
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span className="badge badge-blue hidden sm:inline-flex">DEMONSTRATION DATA</span>
              <span className="text-xs text-navy-500 hidden md:inline">East Coast India · Bulk Coal</span>
            </div>
          </header>
          <main className="flex-1 p-4 md:p-6 overflow-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/decision" element={<DecisionCenter />} />
              <Route path="/forecast" element={<ForecastPage />} />
              <Route path="/vessel" element={<VesselPage />} />
              <Route path="/ports" element={<PortPage />} />
              <Route path="/contract" element={<ContractPage />} />
              <Route path="/idle" element={<IdlePage />} />
              <Route path="/risk" element={<RiskPage />} />
              <Route path="/scenario" element={<ScenarioPage />} />
              <Route path="/map" element={<MapPage />} />
              <Route path="/transparency" element={<TransparencyPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </DecisionProvider>
  )
}
