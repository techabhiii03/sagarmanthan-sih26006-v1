import { useDecision } from '../hooks/useDecision'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function ForecastPage() {
  const { result } = useDecision()

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto card p-8 text-center">
        <p className="text-navy-300 mb-4">Run an evaluation in Decision Center first.</p>
        <Link to="/decision" className="btn-primary">Go to Decision Center</Link>
      </div>
    )
  }

  const models = Object.entries(result.forecast.all_model_comparison || {}).map(([name, m]) => ({
    name,
    mape: m.mape,
    rmse: m.rmse,
    dir_acc: m.dir_acc,
  }))

  const importance = Object.entries(result.forecast.feature_importance || {})
    .map(([k, v]) => ({ feature: k, importance: v }))
    .sort((a, b) => b.importance - a.importance)

  const series = [
    { day: 'Now', rate: result.forecast.current_rate },
    { day: '7d', rate: result.forecast.forecast_7d },
    { day: '14d', rate: result.forecast.forecast_14d },
    { day: '30d', rate: result.forecast.forecast_30d },
    { day: '60d', rate: result.forecast.forecast_60d },
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Freight Forecast Engine</h1>
      <p className="text-navy-400 text-sm">Chronological validation · Model comparison · Feature importance (DEMONSTRATION DATA)</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-xs text-navy-400">Selected Model</div>
          <div className="text-xl font-bold text-ocean-400">{result.forecast.model}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-navy-400">MAPE</div>
          <div className="text-xl font-bold text-white">{result.forecast.mape}%</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-navy-400">RMSE</div>
          <div className="text-xl font-bold text-white">{result.forecast.rmse}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-navy-400">Current Rate</div>
          <div className="text-xl font-bold text-white">${result.forecast.current_rate}/MT</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header"><h2 className="font-semibold">Forecast Horizon</h2></div>
          <div className="p-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334e68" />
                <XAxis dataKey="day" stroke="#829ab1" />
                <YAxis stroke="#829ab1" domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ background: '#243b53', border: '1px solid #486581' }} />
                <Line type="monotone" dataKey="rate" stroke="#0ea5e9" strokeWidth={2} name="USD/MT" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h2 className="font-semibold">Model Comparison (MAPE %)</h2></div>
          <div className="p-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={models}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334e68" />
                <XAxis dataKey="name" stroke="#829ab1" fontSize={11} />
                <YAxis stroke="#829ab1" />
                <Tooltip contentStyle={{ background: '#243b53', border: '1px solid #486581' }} />
                <Bar dataKey="mape" fill="#0ea5e9" name="MAPE %" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h2 className="font-semibold">Feature Importance (%)</h2></div>
        <div className="p-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={importance} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334e68" />
              <XAxis type="number" stroke="#829ab1" />
              <YAxis dataKey="feature" type="category" width={80} stroke="#829ab1" fontSize={11} />
              <Tooltip contentStyle={{ background: '#243b53', border: '1px solid #486581' }} />
              <Bar dataKey="importance" fill="#38bdf8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-white mb-2">Drivers</h3>
        <ul className="space-y-1 text-sm text-navy-300">
          {result.forecast.drivers.map((d, i) => (
            <li key={i}>• {d}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
