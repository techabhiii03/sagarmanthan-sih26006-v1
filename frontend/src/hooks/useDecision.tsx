import React, { createContext, useContext, useState, useCallback } from 'react'
import type { DecisionResult } from '../types'
import { api } from '../services/api'

interface DecisionContextValue {
  result: DecisionResult | null
  loading: boolean
  error: string | null
  lastPayload: any
  evaluate: (payload: any) => Promise<void>
  clear: () => void
}

const DecisionContext = createContext<DecisionContextValue | null>(null)

export function DecisionProvider({ children }: { children: React.ReactNode }) {
  const [result, setResult] = useState<DecisionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastPayload, setLastPayload] = useState<any>(null)

  const evaluate = useCallback(async (payload: any) => {
    setLoading(true)
    setError(null)
    setLastPayload(payload)
    try {
      const data = await api.decision(payload)
      setResult(data)
    } catch (e: any) {
      setError(e.message || 'Evaluation failed')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const clear = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return (
    <DecisionContext.Provider value={{ result, loading, error, lastPayload, evaluate, clear }}>
      {children}
    </DecisionContext.Provider>
  )
}

export function useDecision() {
  const ctx = useContext(DecisionContext)
  if (!ctx) throw new Error('useDecision must be used within DecisionProvider')
  return ctx
}
