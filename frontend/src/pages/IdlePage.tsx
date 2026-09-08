import { useDecision } from '../hooks/useDecision'
import { Link } from 'react-router-dom'
import { Clock, Ship, MapPin, Briefcase } from 'lucide-react'

export default function IdlePage() {
  const { result } = useDecision()
  if (!result) {
    return (
      <div className="max-w-4xl mx-auto card p-8 text-center">
        <p className="text-navy-300 mb-4">Run Decision Center first to see idle & positioning optimization.</p>
        <Link to="/decision" className="btn-primary">Decision Center</Link>
      </div>
    )
  }
  const idle = result.idle

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Idle & Positioning Optimizer</h1>
      <p className="text-navy-400 text-sm">
        Minimize vessel idle time after discharge — wait, reposition, or take alternative employment.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 text-navy-400 text-sm mb-2">
            <Clock size={16} /> Current Expected Idle
          </div>
          <div className="text-3xl font-bold text-amber-400">{idle.current_expected_idle_days} days</div>
        </div>
        <div className="card p-5 border border-ocean-500/30">
          <div className="flex items-center gap-2 text-navy-400 text-sm mb-2">
            <Briefcase size={16} /> Best Strategy
          </div>
          <div className="text-xl font-bold text-ocean-400">{idle.best_strategy}</div>
          <div className="text-sm text-navy-300 mt-1">Idle reduced to {idle.idle_reduced_to_days} days</div>
        </div>
        <div className="card p-5">
          <div className="text-navy-400 text-sm mb-2">Estimated Economic Benefit</div>
          <div className="text-3xl font-bold text-emerald-400">
            ${idle.estimated_economic_benefit_usd?.toLocaleString()}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="font-semibold text-white">Strategy Comparison</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-navy-400 text-left border-b border-navy-700">
                <th className="p-4">Strategy</th>
                <th className="p-4">Idle Days</th>
                <th className="p-4">Economic Impact (USD)</th>
                <th className="p-4">Description</th>
              </tr>
            </thead>
            <tbody>
              {idle.options?.map((o: any) => (
                <tr
                  key={o.strategy}
                  className={`border-b border-navy-800/50 ${
                    o.strategy === idle.best_strategy ? 'bg-ocean-500/10' : ''
                  }`}
                >
                  <td className="p-4 font-medium text-white">
                    {o.strategy}
                    {o.strategy === idle.best_strategy && (
                      <span className="ml-2 badge badge-green">BEST</span>
                    )}
                  </td>
                  <td className="p-4">{Number(o.idle_days).toFixed(1)}</td>
                  <td className={`p-4 font-mono ${o.economic_impact_usd >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {o.economic_impact_usd >= 0 ? '+' : ''}
                    {Math.round(o.economic_impact_usd).toLocaleString()}
                  </td>
                  <td className="p-4 text-navy-400 text-xs max-w-md">{o.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card p-5 text-sm text-navy-400">
        <strong className="text-navy-200">Method:</strong> Options ranked by economic impact = alternative contribution − (idle days × daily hire) − ballast fuel cost.
        Values are algorithmically derived from vessel class hire rates and route distances (demonstration calibration).
      </div>
    </div>
  )
}
