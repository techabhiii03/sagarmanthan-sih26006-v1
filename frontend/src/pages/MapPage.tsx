import { useEffect, useState, useMemo, useCallback } from 'react'
import { MapContainer, TileLayer, Popup, Polyline, CircleMarker, useMap } from 'react-leaflet'
import L from 'leaflet'
import { api } from '../services/api'
import type { Port } from '../types'
import { useDecision } from '../hooks/useDecision'
import { MapPin, Anchor, Navigation, Layers } from 'lucide-react'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    if (points.length >= 2) {
      map.fitBounds(points, { padding: [48, 48], maxZoom: 6 })
    } else if (points.length === 1) {
      map.setView(points[0], 5)
    }
  }, [map, points])
  return null
}

function InvalidateSize() {
  const map = useMap()
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 120)
    const onResize = () => map.invalidateSize()
    window.addEventListener('resize', onResize)
    return () => {
      clearTimeout(t)
      window.removeEventListener('resize', onResize)
    }
  }, [map])
  return null
}

function resolveTileProvider(): { url: string; attribution: string; provider: string; usingFallback: boolean } {
  const provider = (import.meta.env.VITE_MAP_PROVIDER || 'osm').toLowerCase()
  const maptilerKey = import.meta.env.VITE_MAPTILER_API_KEY as string | undefined
  const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN as string | undefined

  if (provider === 'maptiler' && maptilerKey) {
    return {
      url: `https://api.maptiler.com/maps/dataviz-dark/{z}/{x}/{y}.png?key=${maptilerKey}`,
      attribution: '&copy; MapTiler &copy; OpenStreetMap contributors',
      provider: 'maptiler',
      usingFallback: false,
    }
  }
  if (provider === 'mapbox' && mapboxToken) {
    return {
      url: `https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`,
      attribution: '&copy; Mapbox &copy; OpenStreetMap',
      provider: 'mapbox',
      usingFallback: false,
    }
  }
  // Safe default — no API key required
  return {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OSM / Carto',
    provider: 'osm-carto',
    usingFallback: provider === 'maptiler' || provider === 'mapbox',
  }
}

export default function MapPage() {
  const [ports, setPorts] = useState<Port[]>([])
  const [selected, setSelected] = useState<Port | null>(null)
  const [filter, setFilter] = useState<'all' | 'loading' | 'discharge'>('all')
  const [loading, setLoading] = useState(true)
  const { result } = useDecision()
  const { url: tileUrl, attribution: tileAttribution, provider: mapProvider, usingFallback } = resolveTileProvider()


  useEffect(() => {
    api.ports().then(setPorts).catch(console.error).finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    if (filter === 'all') return ports
    return ports.filter((p) => p.type === filter)
  }, [ports, filter])

  const origin = result?.input?.origin
  const dest = result?.input?.destination
  const oPort = ports.find((p) => p.name === origin)
  const dPort = ports.find((p) => p.name === dest)

  const routePoints: [number, number][] = useMemo(() => {
    if (oPort && dPort) return [[oPort.lat, oPort.lon], [dPort.lat, dPort.lon]]
    return []
  }, [oPort, dPort])

  const allPoints: [number, number][] = useMemo(() => {
    if (routePoints.length) return routePoints
    return filtered.map((p) => [p.lat, p.lon] as [number, number])
  }, [routePoints, filtered])

  const onSelect = useCallback((p: Port) => setSelected(p), [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-navy-400">
        Loading maritime map…
      </div>
    )
  }

  return (
    <div className="max-w-[1600px] mx-auto space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Maritime Map</h1>
          <p className="text-navy-400 text-sm mt-1">
            Loading & discharge ports · route · constraints. Tap a port for full particulars.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(['all', 'loading', 'discharge'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-colors ${
                filter === f
                  ? 'bg-ocean-500 text-white'
                  : 'bg-navy-800 text-navy-300 border border-navy-600 hover:bg-navy-700'
              }`}
            >
              {f === 'all' ? 'All ports' : f}
            </button>
          ))}
        </div>
      </div>

      {result && oPort && dPort && (
        <div className="card px-4 py-3 flex flex-wrap items-center gap-3 text-sm">
          <Navigation size={16} className="text-ocean-400 shrink-0" />
          <span className="text-navy-300">
            Active route:{' '}
            <strong className="text-white">{origin}</strong>
            <span className="text-navy-500 mx-1">→</span>
            <strong className="text-white">{dest}</strong>
          </span>
          <span className="badge badge-blue">{result.voyage?.distance_nm ?? '—'} nm</span>
          <span className="badge badge-green">{result.vessel?.recommended}</span>
          {result.port?.overall_feasible ? (
            <span className="badge badge-green">Route feasible</span>
          ) : (
            <span className="badge badge-red">Check constraints</span>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-[520px] lg:min-h-[640px]">
        <div className="lg:col-span-3 order-2 lg:order-1">
          <div className="card h-full flex flex-col max-h-[280px] lg:max-h-none overflow-hidden">
            <div className="card-header py-3">
              <span className="font-semibold text-white text-sm flex items-center gap-2">
                <Layers size={14} /> Ports ({filtered.length})
              </span>
            </div>
            <div className="flex-1 overflow-y-auto divide-y divide-navy-800">
              {filtered.map((p) => {
                const isRoute = p.name === origin || p.name === dest
                const isSel = selected?.name === p.name
                return (
                  <button
                    key={p.name}
                    onClick={() => onSelect(p)}
                    className={`w-full text-left px-4 py-3 transition-colors hover:bg-navy-800/80 ${
                      isSel ? 'bg-ocean-500/15 border-l-2 border-ocean-400' : ''
                    } ${isRoute ? 'bg-navy-800/40' : ''}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-white text-sm truncate">{p.name}</span>
                      <span
                        className={`text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded ${
                          p.type === 'loading'
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-sky-500/20 text-sky-400'
                        }`}
                      >
                        {p.type === 'loading' ? 'Load' : 'Disc'}
                      </span>
                    </div>
                    <div className="text-xs text-navy-400 mt-0.5">
                      {p.country} · Draft {p.max_draft_m} m · Wait {p.typical_waiting_hrs}h
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 order-1 lg:order-2">
          <div className="card overflow-hidden h-[360px] sm:h-[420px] lg:h-full min-h-[360px] relative">
            <MapContainer
              center={[12, 75]}
              zoom={3}
              className="h-full w-full z-0"
              scrollWheelZoom
              style={{ background: '#0a1929', height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution={tileAttribution}
                url={tileUrl}
              />
              <InvalidateSize />
              {allPoints.length > 0 && <FitBounds points={allPoints} />}

              {filtered.map((p) => {
                const isOrigin = p.name === origin
                const isDest = p.name === dest
                const color = isOrigin ? '#f59e0b' : isDest ? '#0ea5e9' : p.type === 'loading' ? '#fbbf24' : '#38bdf8'
                return (
                  <CircleMarker
                    key={p.name}
                    center={[p.lat, p.lon]}
                    radius={isOrigin || isDest ? 10 : 7}
                    pathOptions={{
                      color: '#fff',
                      weight: isOrigin || isDest ? 2 : 1,
                      fillColor: color,
                      fillOpacity: 0.9,
                    }}
                    eventHandlers={{ click: () => onSelect(p) }}
                  >
                    <Popup>
                      <div className="text-sm min-w-[160px]">
                        <strong>{p.name}</strong>
                        <div className="text-xs text-gray-600">{p.country} · {p.type}</div>
                        <div className="mt-1 text-xs">
                          Draft <b>{p.max_draft_m} m</b> · LOA <b>{p.max_loa_m} m</b>
                          <br />
                          Congestion {(p.congestion_index * 100).toFixed(0)}% · Wait {p.typical_waiting_hrs}h
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                )
              })}

              {routePoints.length === 2 && (
                <Polyline
                  positions={routePoints}
                  pathOptions={{ color: '#0ea5e9', weight: 3, dashArray: '10 8', opacity: 0.85 }}
                />
              )}
            </MapContainer>

            <div className="absolute bottom-3 left-3 z-[1000] bg-navy-900/90 backdrop-blur border border-navy-700 rounded-lg px-3 py-2 text-[10px] text-navy-300 space-y-1 pointer-events-none">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Loading
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400" /> Discharge
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 border-t-2 border-dashed border-ocean-400 inline-block" /> Active route
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3 order-3">
          <div className="card h-full min-h-[220px] flex flex-col">
            <div className="card-header py-3">
              <span className="font-semibold text-white text-sm flex items-center gap-2">
                <Anchor size={14} /> Port detail
              </span>
            </div>
            {selected ? (
              <div className="p-4 space-y-3 flex-1 overflow-y-auto">
                <div>
                  <h3 className="text-lg font-bold text-white">{selected.name}</h3>
                  <p className="text-xs text-navy-400">
                    {selected.country} · {selected.type}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <Detail label="Max draft" value={`${selected.max_draft_m} m`} />
                  <Detail label="Max LOA" value={`${selected.max_loa_m} m`} />
                  <Detail label="Max beam" value={`${selected.max_beam_m} m`} />
                  <Detail label="Handling" value={`${(selected.cargo_handling_mt_day / 1000).toFixed(0)}k MT/d`} />
                  <Detail label="Waiting" value={`${selected.typical_waiting_hrs} h`} />
                  <Detail label="Congestion" value={`${(selected.congestion_index * 100).toFixed(0)}%`} />
                </div>
                <div className="space-y-1.5 pt-2 border-t border-navy-800">
                  <div className="text-[10px] uppercase tracking-wider text-navy-500">Vessel feasibility (draft)</div>
                  <FeasRow name="Handysize" draft={10.5} limit={selected.max_draft_m} />
                  <FeasRow name="Supramax" draft={12.5} limit={selected.max_draft_m} />
                  <FeasRow name="Panamax" draft={14.5} limit={selected.max_draft_m} />
                  <FeasRow name="Capesize" draft={18.0} limit={selected.max_draft_m} />
                </div>
                <p className="text-[11px] text-navy-500 leading-relaxed">{selected.notes}</p>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-navy-500 p-6 text-center text-sm">
                <MapPin size={28} className="mb-2 opacity-40" />
                Select a port from the list or map
              </div>
            )}
          </div>
        </div>
      </div>

      <p className="text-[11px] text-navy-500">
        Map tiles: {mapProvider}
        {usingFallback ? ' (API key not configured — using OSM/Carto fallback)' : ''} · Port limits: prototype dataset · Route is display great-circle.
      </p>
    </div>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-navy-800/50 rounded-lg px-2.5 py-2">
      <div className="text-navy-500">{label}</div>
      <div className="font-semibold text-navy-100">{value}</div>
    </div>
  )
}

function FeasRow({ name, draft, limit }: { name: string; draft: number; limit: number }) {
  const ok = draft <= limit + 0.05
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-navy-300">{name}</span>
      <span className={ok ? 'text-emerald-400 font-medium' : 'text-rose-400 font-medium'}>
        {ok ? '✓ Feasible' : `✕ ${draft}m > ${limit}m`}
      </span>
    </div>
  )
}
