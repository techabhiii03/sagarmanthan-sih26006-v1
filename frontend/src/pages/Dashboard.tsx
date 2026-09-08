import { Link } from 'react-router-dom'
import { useDecision } from '../hooks/useDecision'
import { Compass, TrendingUp, Ship, AlertTriangle, Anchor, ArrowRight } from 'lucide-react'

export default function Dashboard() {
  const { result } = useDecision()

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">SagarManthan Dashboard</h1>
        <p className="text-navy-400 text-sm mt-1">
          Intelligent Freight Forecasting & Vessel Chartering Decision Platform — SIH26006
        </p>
      </div>

      {/* Hero CTA */}
      <div className="card p-6 md:p-8 bg-gradient-to-br from-ocean-500/10 to-navy-900 border border-ocean-500/20">
        <h2 className="text-xl font-bold text-white mb-2">From Reactive Spot to Predictive Multi-Voyage</h2>
        <p className="text-navy-300 text-sm max-w-2xl mb-4">
          Enter a cargo requirement and receive a complete decision: market entry timing, optimal vessel type
          (respecting East Coast port constraints), contract mix, idle strategy, risk profile and expected savings.
        </p>
        <Link to="/decision" className="btn-primary inline-flex items-center gap-2">
          Open Decision Center <ArrowRight size={18} />
        </Link>
      </div>

      {/* Quick stats from last evaluation */}
      {result ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Decision" value={result.decision} color={result.decision === 'WAIT' ? 'amber' : result.decision === 'BOOK' ? 'emerald' : 'rose'} />
          <StatCard label="Vessel" value={result.vessel.recommended} color="sky" />
          <StatCard label="Risk" value={`${result.risk.level} (${result.risk.overall})`} color={result.risk.level === 'HIGH' ? 'rose' : 'amber'} />
          <StatCard label="Saving (₹ Cr)" value={String(result.savings.expected_inr_cr)} color="emerald" />
        </div>
      ) : (
        <div className="card p-6 text-center text-navy-400 text-sm">
          No evaluation yet. Go to Decision Center and run the Newcastle → Paradip demo.
        </div>
      )}

      {/* Module grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <ModuleCard to="/forecast" icon={TrendingUp} title="Freight Forecast" desc="7/14/30/60-day rates with XGBoost + baselines, MAPE, feature importance" />
        <ModuleCard to="/vessel" icon={Ship} title="Vessel Optimizer" desc="Handysize → Capesize ranking under draft/LOA/beam constraints" />
        <ModuleCard to="/ports" icon={Anchor} title="Port Intelligence" desc="East Coast ports + origin terminals with congestion & feasibility" />
        <ModuleCard to="/contract" icon={Compass} title="Contract Optimizer" desc="Spot vs 3-voyage vs 6-voyage mix and risk reduction" />
        <ModuleCard to="/risk" icon={AlertTriangle} title="Risk Center" desc="Multi-dimensional freight, port, schedule, bunker risk scores" />
        <ModuleCard to="/scenario" icon={TrendingUp} title="Scenario Analysis" desc="What-if on freight, bunker, waiting, volume, destination" />
      </div>

      <div className="text-xs text-navy-500">
        All recommendations are calculated from models and constraint engines. Monetary figures use demonstration data labelled as such.
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colors: Record<string, string> = {
    amber: 'text-amber-400',
    emerald: 'text-emerald-400',
    rose: 'text-rose-400',
    sky: 'text-sky-400',
  }
  return (
    <div className="card p-4">
      <div className="text-xs text-navy-400 uppercase tracking-wider">{label}</div>
      <div className={`text-xl font-bold mt-1 ${colors[color] || 'text-white'}`}>{value}</div>
    </div>
  )
}

function ModuleCard({ to, icon: Icon, title, desc }: { to: string; icon: any; title: string; desc: string }) {
  return (
    <Link to={to} className="card p-5 hover:border-ocean-500/40 transition-colors block">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-9 h-9 rounded-lg bg-ocean-500/15 flex items-center justify-center">
          <Icon size={18} className="text-ocean-400" />
        </div>
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      <p className="text-sm text-navy-400">{desc}</p>
    </Link>
  )
}
