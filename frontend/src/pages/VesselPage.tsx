import { useDecision } from '../hooks/useDecision'
import { Link } from 'react-router-dom'
import { CheckCircle2, XCircle } from 'lucide-react'

export default function VesselPage() {
  const { result } = useDecision()
  if (!result) {
    return (
      <div className="max-w-4xl mx-auto card p-8 text-center">
        <p className="text-navy-300 mb-4">Run Decision Center first.</p>
        <Link to="/decision" className="btn-primary">Decision Center</Link>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Vessel Optimizer</h1>
      <p className="text-navy-400 text-sm">Minimize total voyage cost subject to origin and destination port constraints (draft, LOA, beam).</p>

      <div className="card p-5">
        <div className="text-sm text-navy-400">Recommended</div>
        <div className="text-3xl font-bold text-ocean-400">{result.vessel.recommended}</div>
        <div className="mt-1 text-navy-300">
          ${result.vessel.cost_per_mt}/MT · Total ${result.vessel.total_cost_usd?.toLocaleString()}
        </div>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-navy-400 text-left border-b border-navy-700">
              <th className="p-4">Vessel</th>
              <th className="p-4">Feasible</th>
              <th className="p-4">Cost/MT</th>
              <th className="p-4">Total Cost</th>
              <th className="p-4">Voyages</th>
              <th className="p-4">Reasons</th>
            </tr>
          </thead>
          <tbody>
            {result.vessel.candidates?.map((c: any) => (
              <tr key={c.vessel} className="border-b border-navy-800/60">
                <td className="p-4 font-medium text-white">
                  {c.vessel}
                  {c.vessel === result.vessel.recommended && <span className="ml-2 badge badge-green">BEST</span>}
                </td>
                <td className="p-4">
                  {c.feasible ? (
                    <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 size={16} /> Yes</span>
                  ) : (
                    <span className="text-rose-400 flex items-center gap-1"><XCircle size={16} /> No</span>
                  )}
                </td>
                <td className="p-4">{c.cost_per_mt != null ? `$${c.cost_per_mt}` : '—'}</td>
                <td className="p-4">{c.total_cost_usd != null ? `$${c.total_cost_usd.toLocaleString()}` : '—'}</td>
                <td className="p-4">{c.voyages_needed ?? '—'}</td>
                <td className="p-4 text-xs text-navy-400 max-w-xs">
                  {(c.rejection_reasons || []).join('; ') || 'All constraints OK'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
