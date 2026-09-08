import type { DecisionResult, Port, Vessel } from '../types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  ports: (type?: string) => request<Port[]>(`/ports${type ? `?type=${type}` : ''}`),
  berths: (port?: string) => request<any[]>(`/berths${port ? `?port=${encodeURIComponent(port)}` : ''}`),
  vessels: () => request<Vessel[]>('/vessels'),
  forecast: (origin: string, vessel: string) =>
    request('/forecast', { method: 'POST', body: JSON.stringify({ origin, vessel }) }),
  decision: (payload: {
    origin: string
    destination: string
    cargo?: string
    cargo_mt?: number
    laycan_start?: string
    bunker_price?: number
    extra_waiting_hrs?: number
    risk_tolerance?: string
    num_voyages?: number
  }) =>
    request<DecisionResult>('/decision/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  scenario: (payload: any) =>
    request<DecisionResult>('/scenario', { method: 'POST', body: JSON.stringify(payload) }),
  vesselOptimize: (payload: any) =>
    request('/vessel/optimize', { method: 'POST', body: JSON.stringify(payload) }),
  portCheck: (payload: any) =>
    request('/port/check', { method: 'POST', body: JSON.stringify(payload) }),
  voyageCost: (payload: any) =>
    request('/voyage/cost', { method: 'POST', body: JSON.stringify(payload) }),
  contract: (payload: any) =>
    request('/contract/optimize', { method: 'POST', body: JSON.stringify(payload) }),
  idle: (payload: any) =>
    request('/idle/optimize', { method: 'POST', body: JSON.stringify(payload) }),
  risk: (payload: any) =>
    request('/risk', { method: 'POST', body: JSON.stringify(payload) }),
}
