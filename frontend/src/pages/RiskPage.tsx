import { useDecision } from '../hooks/useDecision'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function RiskPage() {
  const { result } = useDecision()
  if (!result) {
    return (
      <div className="max-w-4xl mx-auto card p-8 text-center">
        <p className="text-navy-300 mb-4">Run Decision Center first.</p>
        <Link to="/decision" className="btn-primary">Decision Center</Link>
      </div>
    )
  }
  const r = result.risk
  const data = Object.entries(r.dimensions || {}).map(([k, v]) => ({ name: k, score: v }))

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Risk Center</h1>
      <div className="card p-6 flex flex-col md:flex-row md:items-center gap-6">
        <div>
          <div className="text-sm text-navy-400">Overall Risk</div>
          <div className={`text-5xl font-extrabold ${
            r.level === 'HIGH' ? 'text-rose-400' : r.level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
          }`}>{r.overall}</div>
          <div className="text-lg font-semibold text-navy-200">{r.level}</div>
        </div>
        <div className="flex-1 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334e68" />
              <XAxis dataKey="name" stroke="#829ab1" fontSize={11} />
              <YAxis domain={[0, 100]} stroke="#829ab1" />
              <Tooltip contentStyle={{ background: '#243b53', border: '1px solid #486581' }} />
              <Bar dataKey="score" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(r.explanations || {}).map(([k, v]) => (
          <div key={k} className="card p-4">
            <div className="flex justify-between items-center mb-1">
              <span className="font-semibold text-white capitalize">{k}</span>
              <span className="badge badge-amber">{r.dimensions[k]}</span>
            </div>
            <p className="text-sm text-navy-400">{v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
