export default function TransparencyPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Data & Model Transparency</h1>
      <p className="text-navy-400 text-sm">
        Every important figure is calculated. No hardcoded “83% reliability” or arbitrary savings.
      </p>

      <div className="card p-5 space-y-4 text-sm text-navy-300">
        <section>
          <h2 className="font-semibold text-white mb-2">Data Provenance</h2>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>Freight rates:</strong> DEMONSTRATION DATA — synthetic daily series with trend, seasonality, cycles and noise, calibrated to realistic coal freight levels (USD/MT).</li>
            <li><strong>Port constraints:</strong> Prototype dataset of approximate public draft / LOA / beam / handling rates for East Coast India and major loading ports.</li>
            <li><strong>Distances:</strong> Approximate great-circle NM from route table.</li>
            <li><strong>Bunker:</strong> User-adjustable price; consumption from vessel class averages.</li>
          </ul>
        </section>

        <section>
          <h2 className="font-semibold text-white mb-2">Forecast Models</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>Naive, Moving Average, XGBoost</li>
            <li>Chronological 80/20 split (no random shuffle of time series)</li>
            <li>Metrics: MAPE, RMSE, MAE, Directional Accuracy</li>
            <li>Best model selected by validation MAPE</li>
            <li>Feature importance from XGBoost (lag, MA, volatility, calendar)</li>
          </ul>
        </section>

        <section>
          <h2 className="font-semibold text-white mb-2">Decision Logic</h2>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>BOOK / WAIT / AVOID:</strong> Based on forecast delta vs uncertainty band, risk tolerance, volatility.</li>
            <li><strong>Vessel:</strong> Feasible set filtered by port draft/LOA/beam; ranked by total voyage cost.</li>
            <li><strong>Contract:</strong> Spot / 3-voyage / 6-voyage mix optimized on expected cost + risk score.</li>
            <li><strong>Idle:</strong> Wait vs reposition vs alternative employment ranked by economic impact.</li>
            <li><strong>Risk:</strong> Weighted multi-factor score (freight, port, vessel, bunker, weather, schedule, geo).</li>
          </ul>
        </section>

        <section>
          <h2 className="font-semibold text-white mb-2">API Endpoints</h2>
          <pre className="bg-navy-950 p-3 rounded-lg text-xs overflow-x-auto text-navy-200">
{`POST /api/forecast
POST /api/vessel/optimize
POST /api/port/check
POST /api/voyage/cost
POST /api/contract/optimize
POST /api/idle/optimize
POST /api/risk
POST /api/decision/evaluate   ← main orchestration
POST /api/scenario           ← what-if`}
          </pre>
        </section>

        <div className="badge badge-blue">SIH26006 · Ministry of Steel / SAIL · Demonstration Prototype</div>
      </div>
    </div>
  )
}
