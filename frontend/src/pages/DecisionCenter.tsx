import { useState } from 'react'
import { useDecision } from '../hooks/useDecision'
import {
  Play,
  Ship,
  Anchor,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  IndianRupee,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

const ORIGINS = ['Newcastle', 'Gladstone', 'Richards Bay', 'Maputo', 'Taboneo', 'Hampton Roads']
const DESTINATIONS = ['Paradip', 'Dhamra', 'Visakhapatnam', 'Gangavaram', 'Gopalpur', 'Haldia', 'Sagar-Sandheads']
const CARGOS = ['coking_coal', 'thermal_coal', 'iron_ore']

export default function DecisionCenter() {
  const { result, loading, error, evaluate } = useDecision()
  const [form, setForm] = useState({
    origin: 'Newcastle',
    destination: 'Paradip',
    cargo: 'coking_coal',
    cargo_mt: 80000,
    laycan_start: '2026-11-01',
    bunker_price: 520,
    extra_waiting_hrs: 0,
    risk_tolerance: 'medium',
    num_voyages: 6,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    evaluate(form)
  }

  const decisionColor =
    result?.decision === 'WAIT'
      ? 'text-amber-400'
      : result?.decision === 'BOOK'
      ? 'text-emerald-400'
      : 'text-rose-400'

  const decisionBg =
    result?.decision === 'WAIT'
      ? 'from-amber-500/20 to-amber-600/5 border-amber-500/30'
      : result?.decision === 'BOOK'
      ? 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/30'
      : 'from-rose-500/20 to-rose-600/5 border-rose-500/30'

  const forecastChart = result
    ? [
        { day: 'Now', rate: result.forecast.current_rate },
        { day: '7d', rate: result.forecast.forecast_7d },
        { day: '14d', rate: result.forecast.forecast_14d },
        { day: '30d', rate: result.forecast.forecast_30d },
        { day: '60d', rate: result.forecast.forecast_60d },
      ]
    : []

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Decision Center</h1>
        <p className="text-navy-400 text-sm mt-1">
          Enter cargo requirement → receive unified BOOK / WAIT / AVOID recommendation with full reasoning.
        </p>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="card p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="label">Origin (Loading)</label>
            <select
              className="input"
              value={form.origin}
              onChange={(e) => setForm({ ...form, origin: e.target.value })}
            >
              {ORIGINS.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Destination (East Coast)</label>
            <select
              className="input"
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
            >
              {DESTINATIONS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Cargo</label>
            <select
              className="input"
              value={form.cargo}
              onChange={(e) => setForm({ ...form, cargo: e.target.value })}
            >
              {CARGOS.map((c) => (
                <option key={c} value={c}>{c.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Quantity (MT)</label>
            <input
              type="number"
              className="input"
              value={form.cargo_mt}
              onChange={(e) => setForm({ ...form, cargo_mt: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="label">Laycan Start</label>
            <input
              type="date"
              className="input"
              value={form.laycan_start}
              onChange={(e) => setForm({ ...form, laycan_start: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Bunker Price (USD/MT)</label>
            <input
              type="number"
              className="input"
              value={form.bunker_price}
              onChange={(e) => setForm({ ...form, bunker_price: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="label">Extra Waiting (hrs)</label>
            <input
              type="number"
              className="input"
              value={form.extra_waiting_hrs}
              onChange={(e) => setForm({ ...form, extra_waiting_hrs: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="label">Risk Tolerance</label>
            <select
              className="input"
              value={form.risk_tolerance}
              onChange={(e) => setForm({ ...form, risk_tolerance: e.target.value })}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading}>
            <Play size={18} />
            {loading ? 'Evaluating…' : 'Evaluate Requirement'}
          </button>
          <span className="text-xs text-navy-500 self-center">
            Demo tip: Newcastle → Paradip · 80,000 MT · Coking Coal
          </span>
        </div>
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
            {error}
          </div>
        )}
      </form>

      {/* Result */}
      {result && (
        <div className="space-y-6 animate-in fade-in">
          {/* Big Decision Card */}
          <div className={`card p-6 md:p-8 bg-gradient-to-br ${decisionBg} border`}>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <div className="text-sm font-medium text-navy-400 uppercase tracking-wider mb-2">
                  SagarManthan Decision
                </div>
                <div className={`text-5xl md:text-6xl font-extrabold ${decisionColor}`}>
                  {result.decision}
                </div>
                <div className="mt-2 text-navy-300 text-sm">
                  Confidence: <span className="font-semibold text-white">{(result.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-navy-400">Current Freight</div>
                  <div className="text-xl font-bold text-white">${result.forecast.current_rate}/MT</div>
                </div>
                <div>
                  <div className="text-navy-400">Forecast 14d</div>
                  <div className="text-xl font-bold text-white">${result.forecast.forecast_14d}/MT</div>
                </div>
                <div>
                  <div className="text-navy-400">Best Entry</div>
                  <div className="text-lg font-semibold text-white">{result.market_entry.recommended_entry_window}</div>
                </div>
                <div>
                  <div className="text-navy-400">Recommended Vessel</div>
                  <div className="text-xl font-bold text-ocean-400">{result.vessel.recommended}</div>
                </div>
                <div>
                  <div className="text-navy-400">Risk</div>
                  <div className={`text-lg font-semibold ${
                    result.risk.level === 'HIGH' ? 'text-rose-400' : result.risk.level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
                  }`}>{result.risk.level} ({result.risk.overall})</div>
                </div>
                <div>
                  <div className="text-navy-400">Expected Saving</div>
                  <div className="text-xl font-bold text-emerald-400 flex items-center gap-1">
                    <IndianRupee size={18} />
                    {result.savings.expected_inr_cr} Cr
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Why */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-white">Why this recommendation?</h2>
            </div>
            <ul className="p-5 space-y-2">
              {result.explanation.map((e, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-navy-200">
                  <CheckCircle2 size={16} className="text-ocean-400 mt-0.5 shrink-0" />
                  {e}
                </li>
              ))}
            </ul>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Forecast chart */}
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-white">Freight Forecast</h2>
                <span className="badge badge-blue">{result.forecast.model} · MAPE {result.forecast.mape}%</span>
              </div>
              <div className="p-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334e68" />
                    <XAxis dataKey="day" stroke="#829ab1" fontSize={12} />
                    <YAxis stroke="#829ab1" fontSize={12} domain={['auto', 'auto']} />
                    <Tooltip
                      contentStyle={{ background: '#243b53', border: '1px solid #486581', borderRadius: 8 }}
                      labelStyle={{ color: '#d9e2ec' }}
                    />
                    <Line type="monotone" dataKey="rate" stroke="#0ea5e9" strokeWidth={2} dot={{ r: 4 }} name="USD/MT" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="px-5 pb-4 text-xs text-navy-400 space-y-1">
                {result.forecast.drivers.map((d, i) => (
                  <div key={i}>• {d}</div>
                ))}
              </div>
            </div>

            {/* Vessel comparison */}
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-white">Vessel Feasibility & Cost</h2>
              </div>
              <div className="p-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-navy-400 text-left border-b border-navy-700">
                      <th className="pb-2 font-medium">Vessel</th>
                      <th className="pb-2 font-medium">Status</th>
                      <th className="pb-2 font-medium">Cost/MT</th>
                      <th className="pb-2 font-medium">Voyages</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.vessel.candidates?.map((c: any) => (
                      <tr key={c.vessel} className="border-b border-navy-800/50">
                        <td className="py-2.5 font-medium text-white">
                          {c.vessel}
                          {c.vessel === result.vessel.recommended && (
                            <span className="ml-2 badge badge-green">REC</span>
                          )}
                        </td>
                        <td className="py-2.5">
                          {c.feasible ? (
                            <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 size={14} /> Feasible</span>
                          ) : (
                            <span className="text-rose-400 flex items-center gap-1"><XCircle size={14} /> Rejected</span>
                          )}
                        </td>
                        <td className="py-2.5 text-navy-200">
                          {c.cost_per_mt != null ? `$${c.cost_per_mt}` : '—'}
                        </td>
                        <td className="py-2.5 text-navy-200">{c.voyages_needed ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {/* Rejection reasons */}
                {result.vessel.candidates
                  ?.filter((c: any) => !c.feasible)
                  .map((c: any) => (
                    <div key={c.vessel + '-r'} className="mt-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
                      <strong>{c.vessel} rejected:</strong>
                      <ul className="mt-1 list-disc list-inside">
                        {(c.rejection_reasons || []).map((r: string, i: number) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
              </div>
            </div>
          </div>

          {/* Contract + Idle + Risk row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card p-5">
              <div className="flex items-center gap-2 text-navy-400 text-sm mb-3">
                <FileIcon /> Contract Strategy
              </div>
              <div className="text-lg font-bold text-white">{result.contract.recommended}</div>
              <div className="mt-2 text-sm text-navy-300">
                Spot exposure: {(result.contract.spot_exposure * 100).toFixed(0)}%
              </div>
              <div className="mt-1 text-sm text-emerald-400">
                Savings vs pure spot: ${(result.contract.projected_savings_vs_spot_usd / 1e6).toFixed(2)}M
              </div>
              <div className="mt-3 flex gap-1 flex-wrap">
                {Object.entries(result.contract.recommended_mix || {}).map(([k, v]) => (
                  <span key={k} className="badge badge-blue">{k}: {((v as number) * 100).toFixed(0)}%</span>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-2 text-navy-400 text-sm mb-3">
                <Clock size={16} /> Idle & Positioning
              </div>
              <div className="text-lg font-bold text-white">{result.idle.best_strategy}</div>
              <div className="mt-2 text-sm text-navy-300">
                Idle: {result.idle.current_expected_idle_days}d → {result.idle.idle_reduced_to_days}d
              </div>
              <div className="mt-1 text-sm text-emerald-400">
                Benefit: ${result.idle.estimated_economic_benefit_usd.toLocaleString()}
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-2 text-navy-400 text-sm mb-3">
                <AlertTriangle size={16} /> Risk Profile
              </div>
              <div className={`text-2xl font-bold ${
                result.risk.level === 'HIGH' ? 'text-rose-400' : result.risk.level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {result.risk.overall}/100
              </div>
              <div className="mt-2 space-y-1">
                {result.risk.top_risks?.slice(0, 3).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-xs">
                    <span className="text-navy-400 capitalize">{k}</span>
                    <span className="text-navy-200">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Voyage economics */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-white">Voyage Economics</h2>
              <span className="text-xs text-navy-400">{result.voyage.distance_nm} nm</span>
            </div>
            <div className="p-5 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-navy-400">Total Cost</div>
                <div className="text-lg font-bold text-white">${result.voyage.total_voyage_cost_usd.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-navy-400">Cost / MT</div>
                <div className="text-lg font-bold text-white">${result.voyage.cost_per_mt_usd}</div>
              </div>
              <div>
                <div className="text-navy-400">Freight</div>
                <div className="text-lg font-semibold text-navy-200">${result.voyage.freight_cost_usd.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-navy-400">Bunker</div>
                <div className="text-lg font-semibold text-navy-200">${result.voyage.bunker_cost_usd.toLocaleString()}</div>
              </div>
            </div>
            {result.voyage.breakdown && (
              <div className="px-5 pb-5 flex flex-wrap gap-2">
                {Object.entries(result.voyage.breakdown).map(([k, v]) => (
                  <span key={k} className="badge badge-blue">{k.replace('_pct','')}: {v}%</span>
                ))}
              </div>
            )}
          </div>

          <div className="text-xs text-navy-500 border-t border-navy-800 pt-4">
            Data provenance: {result.data_provenance?.note} · Freight source: {result.data_provenance?.freight}
          </div>
        </div>
      )}
    </div>
  )
}

function FileIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}
