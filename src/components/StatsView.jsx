import { useMemo } from "react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import {
  CATEGORY_CONFIG, NATIONAL_AVERAGE,
  getScoreColor, getAccreditationColor, getScoreLabel,
} from "../data/hospitalData";
import { useTheme } from "../context/ThemeContext";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-label">{label}</span>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="chart-tooltip-row">
          <span className="chart-tooltip-dot" style={{ backgroundColor: entry.color }} />
          <span>{entry.name}: </span>
          <strong>{entry.value}%</strong>
        </div>
      ))}
    </div>
  );
}

function ScoreRing({ score }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);

  return (
    <div className="score-ring-container">
      <svg className="score-ring-svg" viewBox="0 0 128 128">
        <circle className="score-ring-track" cx="64" cy="64" r={radius} fill="none" strokeWidth="8" />
        <circle
          className="score-ring-progress"
          cx="64" cy="64" r={radius}
          fill="none" strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 64 64)"
          style={{ stroke: color }}
        />
        <text className="score-ring-value" x="64" y="58" textAnchor="middle" dominantBaseline="central">
          {score}%
        </text>
        <text className="score-ring-label" x="64" y="78" textAnchor="middle">
          {getScoreLabel(score)}
        </text>
      </svg>
    </div>
  );
}

function CategoryCard({ config, hospitalScore, nationalScore }) {
  const diff = hospitalScore - nationalScore;
  const color = getScoreColor(hospitalScore);

  return (
    <div className="category-card">
      <div className="category-card-header">
        <span className="category-card-icon">{config.icon}</span>
        <span className="category-card-name">{config.label}</span>
      </div>
      <div className="category-card-scores">
        <span className="category-card-value" style={{ color }}>{hospitalScore}%</span>
        <span className={`category-card-diff ${diff >= 0 ? "category-card-diff-positive" : "category-card-diff-negative"}`}>
          {diff >= 0 ? "▲" : "▼"} {Math.abs(diff)} pts vs moy.
        </span>
      </div>
      <div className="category-card-bar-track">
        <div className="category-card-bar-fill" style={{ width: `${hospitalScore}%`, backgroundColor: color }} />
      </div>
      <div className="category-card-meta">
        <span>Poids: {(config.weight * 100).toFixed(0)}%</span>
        <span>Moy. nationale: {nationalScore}%</span>
      </div>
    </div>
  );
}

export default function StatsView({ hospital, onBack }) {
  const { darkMode } = useTheme();

  const chartData = useMemo(
    () => CATEGORY_CONFIG.map((cat) => ({
      category: cat.labelShort,
      fullLabel: cat.label,
      hospital: hospital.scores[cat.key],
      national: NATIONAL_AVERAGE[cat.key],
      fullMark: 100,
    })),
    [hospital]
  );

  const axisColor = darkMode ? "#94a3b8" : "#64748b";
  const gridColor = darkMode ? "#334155" : "#e2e8f0";

  return (
    <div className="stats-view">
      <button className="stats-back-btn" onClick={onBack}>
        <svg className="stats-back-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5m0 0l7 7m-7-7l7-7" />
        </svg>
        <span>Retour à la carte</span>
      </button>

      <div className="stats-header-card">
        <div className="stats-header-info">
          <div className="stats-header-top">
            <span className="stats-accreditation-badge" style={{ backgroundColor: getAccreditationColor(hospital.accreditationLevel) }}>
              Niveau {hospital.accreditationLevel}
            </span>
            <span className="stats-compliance-tag" style={{
              backgroundColor: hospital.globalScore >= 70 ? "#d1fae5" : "#fee2e2",
              color: hospital.globalScore >= 70 ? "#065f46" : "#991b1b",
            }}>
              {hospital.globalScore >= 70 ? "Conforme" : "Non conforme"}
            </span>
          </div>
          <h1 className="stats-hospital-name">{hospital.name}</h1>
          <p className="stats-hospital-label">{hospital.accreditationLabel}</p>

          <div className="stats-meta-grid">
            <div className="stats-meta-item"><span className="stats-meta-icon">📍</span><span>{hospital.city}, {hospital.region}</span></div>
            <div className="stats-meta-item"><span className="stats-meta-icon">🏥</span><span>{hospital.type}</span></div>
            <div className="stats-meta-item"><span className="stats-meta-icon">🛏️</span><span>{hospital.beds} lits</span></div>
            <div className="stats-meta-item"><span className="stats-meta-icon">📋</span><span>Audit: {hospital.lastAudit}</span></div>
            <div className="stats-meta-item"><span className="stats-meta-icon">👤</span><span>{hospital.auditor}</span></div>
            <div className="stats-meta-item"><span className="stats-meta-icon">🔬</span><span>Service: {hospital.service}</span></div>
          </div>
        </div>
        <ScoreRing score={hospital.globalScore} />
      </div>

      <div className="stats-summary-row">
        <div className="stats-summary-card">
          <span className="stats-summary-card-label">Score Global</span>
          <span className="stats-summary-card-value" style={{ color: getScoreColor(hospital.globalScore) }}>{hospital.globalScore}%</span>
          <span className="stats-summary-card-sub">Moy. nationale: {NATIONAL_AVERAGE.global}%</span>
        </div>
        <div className="stats-summary-card">
          <span className="stats-summary-card-label">Incidents Totaux</span>
          <span className="stats-summary-card-value stats-summary-card-value-neutral">{hospital.totalIncidents}</span>
          <span className="stats-summary-card-sub">sur 12 derniers mois</span>
        </div>
        <div className="stats-summary-card">
          <span className="stats-summary-card-label">Incidents Critiques</span>
          <span className="stats-summary-card-value" style={{ color: hospital.criticalIncidents > 0 ? "#ef4444" : "#10b981" }}>
            {hospital.criticalIncidents}
          </span>
          <span className="stats-summary-card-sub">{hospital.criticalIncidents === 0 ? "Aucun incident critique" : "Attention requise"}</span>
        </div>
      </div>

      <div className="stats-charts-row">
        <div className="stats-chart-card">
          <h2 className="stats-chart-title">Profil de Conformité (Radar)</h2>
          <p className="stats-chart-subtitle">Comparaison avec la moyenne nationale</p>
          <div className="stats-chart-body">
            <ResponsiveContainer width="100%" height={340}>
              <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="72%">
                <PolarGrid stroke={gridColor} />
                <PolarAngleAxis dataKey="category" tick={{ fill: axisColor, fontSize: 12, fontWeight: 500 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: axisColor, fontSize: 10 }} axisLine={false} />
                <Radar name="Hôpital" dataKey="hospital" stroke="#10b981" fill="#10b981" fillOpacity={0.25} strokeWidth={2} />
                <Radar name="Moyenne Nationale" dataKey="national" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.10} strokeWidth={2} strokeDasharray="6 4" />
                <Legend wrapperStyle={{ fontSize: 12, color: axisColor }} />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="stats-chart-card">
          <h2 className="stats-chart-title">Scores par Catégorie (Barres)</h2>
          <p className="stats-chart-subtitle">Vert = hôpital · Gris = moyenne nationale</p>
          <div className="stats-chart-body">
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }} barCategoryGap="22%">
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="category" tick={{ fill: axisColor, fontSize: 11 }} axisLine={{ stroke: gridColor }} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: axisColor, fontSize: 11 }} axisLine={{ stroke: gridColor }} tickLine={false} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12, color: axisColor }} />
                <Bar dataKey="hospital" name="Hôpital" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={40} />
                <Bar dataKey="national" name="Moyenne Nationale" fill="#64748b" radius={[4, 4, 0, 0]} maxBarSize={40} opacity={0.55} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="stats-categories-section">
        <h2 className="stats-section-title">Détail par Catégorie</h2>
        <div className="stats-categories-grid">
          {CATEGORY_CONFIG.map((cat) => (
            <CategoryCard
              key={cat.key}
              config={cat}
              hospitalScore={hospital.scores[cat.key]}
              nationalScore={NATIONAL_AVERAGE[cat.key]}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
