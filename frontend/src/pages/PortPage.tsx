import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Port } from '../types'

export default function PortPage() {
  const [ports, setPorts] = useState<Port[]>([])
  const [berths, setBerths] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.ports(), api.berths()])
      .then(([p, b]) => {
        setPorts(p)
        setBerths(b)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-navy-400">Loading ports…</div>

  const east = ports.filter((p) => p.country === 'India')
  const load = ports.filter((p) => p.country !== 'India')

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Port Intelligence</h1>
      <p className="text-navy-400 text-sm">
        East Coast discharge ports, loading terminals, and berth-level draft / LOA / beam limits.
      </p>

      <h2 className="text-lg font-semibold text-white">Indian East Coast (Discharge)</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {east.map((p) => (
          <PortCard key={p.name} port={p} berths={berths.filter((b) => b.port === p.name)} />
        ))}
      </div>

      <h2 className="text-lg font-semibold text-white mt-8">Loading Origins</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {load.map((p) => (
          <PortCard key={p.name} port={p} berths={[]} />
        ))}
      </div>

      {berths.length > 0 && (
        <>
          <h2 className="text-lg font-semibold text-white mt-8">Berth Constraint Register</h2>
          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-navy-400 text-left border-b border-navy-700">
                  <th className="p-3">Port</th>
                  <th className="p-3">Berth</th>
                  <th className="p-3">Draft</th>
                  <th className="p-3">LOA</th>
                  <th className="p-3">Beam</th>
                  <th className="p-3">Wait</th>
                  <th className="p-3">Notes</th>
                </tr>
              </thead>
              <tbody>
                {berths.map((b) => (
                  <tr key={b.berth_key} className="border-b border-navy-800/50">
                    <td className="p-3 text-white">{b.port}</td>
                    <td className="p-3 text-navy-200">{b.display_name}</td>
                    <td className="p-3">{b.max_draft_m} m</td>
                    <td className="p-3">{b.max_loa_m} m</td>
                    <td className="p-3">{b.max_beam_m} m</td>
                    <td className="p-3">{b.waiting_hours_typical} h</td>
                    <td className="p-3 text-xs text-navy-400 max-w-xs">{b.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function PortCard({ port, berths }: { port: Port; berths: any[] }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-bold text-white">{port.name}</h3>
          <div className="text-xs text-navy-400">{port.country} · {port.type}</div>
        </div>
        <span className={`badge ${port.congestion_index > 0.5 ? 'badge-amber' : 'badge-green'}`}>
          Congestion {(port.congestion_index * 100).toFixed(0)}%
        </span>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <div>
          <div className="text-navy-500">Draft</div>
          <div className="font-semibold text-navy-200">{port.max_draft_m} m</div>
        </div>
        <div>
          <div className="text-navy-500">LOA</div>
          <div className="font-semibold text-navy-200">{port.max_loa_m} m</div>
        </div>
        <div>
          <div className="text-navy-500">Beam</div>
          <div className="font-semibold text-navy-200">{port.max_beam_m} m</div>
        </div>
        <div>
          <div className="text-navy-500">Handling</div>
          <div className="font-semibold text-navy-200">{(port.cargo_handling_mt_day / 1000).toFixed(0)}k MT/d</div>
        </div>
        <div>
          <div className="text-navy-500">Waiting</div>
          <div className="font-semibold text-navy-200">{port.typical_waiting_hrs} h</div>
        </div>
      </div>
      {berths.length > 0 && (
        <div className="mt-3 pt-3 border-t border-navy-800">
          <div className="text-[10px] uppercase text-navy-500 mb-1">Berths</div>
          {berths.map((b) => (
            <div key={b.berth_key} className="text-xs text-navy-300 flex justify-between gap-2">
              <span>{b.display_name}</span>
              <span className="text-navy-400">{b.max_draft_m} m draft</span>
            </div>
          ))}
        </div>
      )}
      <p className="mt-3 text-xs text-navy-500">{port.notes}</p>
    </div>
  )
}
