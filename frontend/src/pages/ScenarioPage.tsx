import { useState } from 'react'
import { useDecision } from '../hooks/useDecision'
import { api } from '../services/api'
import type { DecisionResult } from '../types'

export default function ScenarioPage() {
  const { result, lastPayload } = useDecision()
  const [scenarioResult, setScenarioResult] = useState<DecisionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [shocks, setShocks] = useState({
    freight_pct_change: 0,
    bunker_pct_change: 0,
    extra_waiting_hrs: 0,
    cargo_mt_override: null as number | null,
    destination_override: '' as string,
  })

  const run = async () => {
    if (!lastPayload) return
    setLoading(true)
    try {
      const data = await api.scenario({
        base: lastPayload,
        ...shocks,
        destination_override: shocks.destination_override || null,
        cargo_mt_override: shocks.cargo_mt_override,
      })
      setScenarioResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto card p-8 text-center text-navy-300">
        Evaluate a requirement in Decision Center first, then apply what-if shocks here.
      </div>
    )
  }

  const display = scenarioResult || result

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Scenario Analysis</h1>
      <p className="text-navy-400 text-sm">Change assumptions and recompute the full recommendation.</p>

      <div className="card p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="label">Freight shock (%)</label>
          <input type="number" className="input" value={shocks.freight_pct_change}
            onChange={(e) => setShocks({ ...shocks, freight_pct_change: Number(e.target.value) })} />
        </div>
        <div>
          <label className="label">Bunker shock (%)</label>
          <input type="number" className="input" value={shocks.bunker_pct_change}
            onChange={(e) => setShocks({ ...shocks, bunker_pct_change: Number(e.target.value) })} />
        </div>
        <div>
          <label className="label">Extra waiting (hrs)</label>
          <input type="number" className="input" value={shocks.extra_waiting_hrs}
            onChange={(e) => setShocks({ ...shocks, extra_waiting_hrs: Number(e.target.value) })} />
        </div>
        <div>
          <label className="label">Cargo MT override</label>
          <input type="number" className="input" placeholder="e.g. 150000"
            onChange={(e) => setShocks({ ...shocks, cargo_mt_override: e.target.value ? Number(e.target.value) : null })} />
        </div>
        <div>
          <label className="label">Destination override</label>
          <select className="input" value={shocks.destination_override}
            onChange={(e) => setShocks({ ...shocks, destination_override: e.target.value })}>
            <option value="">Keep original</option>
            {['Paradip', 'Dhamra', 'Visakhapatnam', 'Gangavaram', 'Gopalpur', 'Haldia'].map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <button className="btn-primary w-full" onClick={run} disabled={loading}>
            {loading ? 'Recomputing…' : 'Apply Scenario'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-xs text-navy-400">Decision</div>
          <div className="text-xl font-bold text-amber-400">{display.decision}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-navy-400">Vessel</div>
          <div className="text-xl font-bold text-ocean-400">{display.vessel.recommended}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-navy-400">Risk</div>
          <div className="text-xl font-bold text-white">{display.risk.level} ({display.risk.overall})</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-navy-400">Saving ₹ Cr</div>
          <div className="text-xl font-bold text-emerald-400">{display.savings.expected_inr_cr}</div>
        </div>
      </div>
    </div>
  )
}
