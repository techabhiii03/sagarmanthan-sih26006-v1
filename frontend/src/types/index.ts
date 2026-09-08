export interface DecisionResult {
  decision: 'BOOK' | 'WAIT' | 'AVOID'
  confidence: number
  timestamp: string
  input: {
    origin: string
    destination: string
    cargo: string
    cargo_mt: number
    laycan_start?: string
    bunker_price: number
    extra_waiting_hrs: number
  }
  forecast: {
    current_rate: number
    forecast_7d: number
    forecast_14d: number
    forecast_30d: number
    forecast_60d: number
    mape: number
    rmse: number
    model: string
    feature_importance: Record<string, number>
    drivers: string[]
    all_model_comparison: Record<string, { mape: number; rmse: number; mae: number; dir_acc: number }>
  }
  market_entry: {
    decision: string
    confidence: number
    current_rate: number
    forecast_14d: number
    recommended_entry_window: string
    latest_safe_booking_date: string
    expected_saving_per_mt_usd: number
    reasons: string[]
  }
  vessel: {
    recommended: string
    cost_per_mt: number
    total_cost_usd: number
    candidates: any[]
    ranked_feasible: { vessel: string; total_cost_usd: number; cost_per_mt: number; voyages_needed: number }[]
  }
  port: {
    origin_feasible: boolean
    destination_feasible: boolean
    overall_feasible: boolean
    details: any
  }
  voyage: {
    total_voyage_cost_usd: number
    cost_per_mt_usd: number
    distance_nm: number
    bunker_cost_usd: number
    freight_cost_usd: number
    waiting_cost_usd: number
    breakdown: Record<string, number>
  }
  contract: {
    recommended: string
    recommended_mix: Record<string, number>
    projected_savings_vs_spot_usd: number
    spot_exposure: number
    risk_reduction_points: number
    all_strategies: any[]
  }
  idle: {
    current_expected_idle_days: number
    best_strategy: string
    idle_reduced_to_days: number
    estimated_economic_benefit_usd: number
    options: any[]
  }
  risk: {
    overall: number
    level: string
    dimensions: Record<string, number>
    explanations: Record<string, string>
    top_risks: [string, number][]
  }
  savings: {
    expected_usd: number
    expected_inr_cr: number
    components: { from_timing_usd: number; from_contract_usd: number }
  }
  explanation: string[]
  data_provenance: Record<string, string>
}

export interface Port {
  name: string
  country: string
  type: string
  lat: number
  lon: number
  max_draft_m: number
  max_loa_m: number
  max_beam_m: number
  cargo_handling_mt_day: number
  typical_waiting_hrs: number
  congestion_index: number
  compatible_cargo: string[]
  notes: string
}

export interface Vessel {
  name: string
  typical_dwt: number
  loa_m: number
  beam_m: number
  draft_laden_m: number
  speed_kn: number
  laden_consumption_mt_day: number
}
