import { useDecision } from '../hooks/useDecision'
import { Link } from 'react-router-dom'

export default function ContractPage() {
  const { result } = useDecision()
  if (!result) {
    return (
      <div className="max-w-4xl mx-auto card p-8 text-center">
        <p className="text-navy-300 mb-4">Run Decision Center first.</p>
        <Link to="/decision" className="btn-primary">Decision Center</Link>
      </div>
    )
  }
  const c = result.contract

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Contract Optimizer</h1>
      <p className="text-navy-400 text-sm">Transition from pure spot to multi-voyage cover. Calculated mix based on forecast & volatility.</p>

      <div className="card p-6">
        <div className="text-sm text-navy-400">Recommended Strategy</div>
        <div className="text-2xl font-bold text-ocean-400">{c.recommended}</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(c.recommended_mix || {}).map(([k, v]) => (
            <span key={k} className="badge badge-blue">{k}: {((v as number) * 100).toFixed(0)}%</span>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-navy-400">Projected Savings vs Spot</div>
            <div className="text-lg font-bold text-emerald-400">${(c.projected_savings_vs_spot_usd / 1e6).toFixed(2)}M</div>
          </div>
          <div>
            <div className="text-navy-400">Spot Exposure</div>
            <div className="text-lg font-bold text-white">{(c.spot_exposure * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-navy-400">Risk Reduction</div>
            <div className="text-lg font-bold text-white">{c.risk_reduction_points} pts</div>
          </div>
        </div>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-navy-400 border-b border-navy-700 text-left">
              <th className="p-4">Strategy</th>
              <th className="p-4">Mix</th>
              <th className="p-4">Expected Cost</th>
              <th className="p-4">Spot %</th>
              <th className="p-4">Risk Score</th>
            </tr>
          </thead>
          <tbody>
            {c.all_strategies?.map((s: any) => (
              <tr key={s.name} className="border-b border-navy-800/50">
                <td className="p-4 font-medium text-white">{s.name}</td>
                <td className="p-4 text-xs">
                  {Object.entries(s.mix).map(([k, v]) => `${k} ${((v as number)*100).toFixed(0)}%`).join(' · ')}
                </td>
                <td className="p-4">${(s.expected_cost_usd / 1e6).toFixed(2)}M</td>
                <td className="p-4">{(s.spot_exposure * 100).toFixed(0)}%</td>
                <td className="p-4">{s.risk_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
