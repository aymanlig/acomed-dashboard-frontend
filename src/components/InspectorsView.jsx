import { useState } from "react";
import { useTheme } from "../context/ThemeContext";

// ── Static mock data ──────────────────────────────────────────────────────────
const INSPECTORS = [
  {
    id: 1,
    name: "Dr. Amina Benchekroun",
    speciality: "Hygiène & Infections",
    region: "Souss-Massa",
    assignedHospital: "Hôpital Régional Hassan II",
    status: "active",
    lastMission: "2024-11-15",
    missionsCompleted: 18,
    avatar: "AB",
    avatarColor: "#10b981",
  },
  {
    id: 2,
    name: "Dr. Youssef El Alaoui",
    speciality: "Sécurité Chirurgicale",
    region: "Souss-Massa",
    assignedHospital: "Hôpital Préfectoral Inezgane",
    status: "on_mission",
    lastMission: "2024-10-22",
    missionsCompleted: 12,
    avatar: "YA",
    avatarColor: "#3b82f6",
  },
  {
    id: 3,
    name: "Dr. Fatima-Zahra Tazi",
    speciality: "Pédiatrie & Conformité",
    region: "Souss-Massa",
    assignedHospital: "Polyclinique CNSS Agadir",
    status: "active",
    lastMission: "2024-12-03",
    missionsCompleted: 27,
    avatar: "FT",
    avatarColor: "#8b5cf6",
  },
  {
    id: 4,
    name: "Ing. Karim Moussaoui",
    speciality: "Maintenance & Équipements",
    region: "Marrakech-Safi",
    assignedHospital: "CHU Mohammed VI",
    status: "on_mission",
    lastMission: "2024-12-10",
    missionsCompleted: 9,
    avatar: "KM",
    avatarColor: "#f59e0b",
  },
  {
    id: 5,
    name: "Dr. Nadia Ouhaddou",
    speciality: "Gestion des Médicaments",
    region: "Casablanca-Settat",
    assignedHospital: "Hôpital Ibn Rochd",
    status: "inactive",
    lastMission: "2024-09-30",
    missionsCompleted: 34,
    avatar: "NO",
    avatarColor: "#64748b",
  },
  {
    id: 6,
    name: "Dr. Rachid Benali",
    speciality: "Sécurité Incendie",
    region: "Rabat-Salé-Kénitra",
    assignedHospital: "CHU Ibn Sina",
    status: "active",
    lastMission: "2024-11-28",
    missionsCompleted: 21,
    avatar: "RB",
    avatarColor: "#ef4444",
  },
];

const STATUS_CONFIG = {
  active:     { label: "Actif",       bg: "rgba(16,185,129,0.12)",  color: "#10b981", dot: "#10b981" },
  on_mission: { label: "En Mission",  bg: "rgba(245,158,11,0.12)",  color: "#f59e0b", dot: "#f59e0b" },
  inactive:   { label: "Inactif",     bg: "rgba(148,163,184,0.12)", color: "#94a3b8", dot: "#94a3b8" },
};

// ── Sub-components ────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.inactive;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: "0.375rem",
      padding: "0.25rem 0.625rem",
      borderRadius: "9999px",
      fontSize: "0.75rem", fontWeight: 700,
      backgroundColor: cfg.bg, color: cfg.color,
    }}>
      <span style={{
        width: "0.5rem", height: "0.5rem",
        borderRadius: "50%",
        backgroundColor: cfg.dot,
        flexShrink: 0,
      }} />
      {cfg.label}
    </span>
  );
}

function InspectorCard({ inspector }) {
  return (
    <div className="inspector-card">
      <div className="inspector-card-left">
        <div
          className="inspector-avatar"
          style={{ background: inspector.avatarColor }}
        >
          {inspector.avatar}
        </div>
        <div className="inspector-info">
          <span className="inspector-name">{inspector.name}</span>
          <span className="inspector-speciality">{inspector.speciality}</span>
        </div>
      </div>

      <div className="inspector-meta">
        <div className="inspector-meta-item">
          <span className="inspector-meta-icon">📍</span>
          <span>{inspector.region}</span>
        </div>
        <div className="inspector-meta-item">
          <span className="inspector-meta-icon">🏥</span>
          <span>{inspector.assignedHospital}</span>
        </div>
        <div className="inspector-meta-item">
          <span className="inspector-meta-icon">📋</span>
          <span>Dernier audit: {inspector.lastMission}</span>
        </div>
      </div>

      <div className="inspector-stats">
        <div className="inspector-stat-badge">
          <span className="inspector-stat-value">{inspector.missionsCompleted}</span>
          <span className="inspector-stat-label">Missions</span>
        </div>
        <StatusBadge status={inspector.status} />
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function InspectorsView() {
  const { darkMode } = useTheme();
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = INSPECTORS.filter((ins) => {
    const matchStatus = filter === "all" || ins.status === filter;
    const matchSearch = ins.name.toLowerCase().includes(search.toLowerCase())
      || ins.region.toLowerCase().includes(search.toLowerCase())
      || ins.speciality.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  const counts = {
    total:      INSPECTORS.length,
    active:     INSPECTORS.filter((i) => i.status === "active").length,
    on_mission: INSPECTORS.filter((i) => i.status === "on_mission").length,
    inactive:   INSPECTORS.filter((i) => i.status === "inactive").length,
  };

  return (
    <div className="inspectors-view">
      {/* ── Header ── */}
      <div className="inspectors-header">
        <div>
          <h1 className="inspectors-title">Liste des Inspecteurs</h1>
          <p className="inspectors-subtitle">
            Gérez et suivez les {counts.total} inspecteurs accrédités ACOMED
          </p>
        </div>
        <button className="inspectors-add-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: "1rem", height: "1rem" }}>
            <path d="M12 5v14M5 12h14" />
          </svg>
          Ajouter
        </button>
      </div>

      {/* ── KPI strip ── */}
      <div className="inspectors-kpi-row">
        <div className="inspectors-kpi-card">
          <span className="inspectors-kpi-value">{counts.total}</span>
          <span className="inspectors-kpi-label">Total</span>
        </div>
        <div className="inspectors-kpi-card">
          <span className="inspectors-kpi-value" style={{ color: "#10b981" }}>{counts.active}</span>
          <span className="inspectors-kpi-label">Actifs</span>
        </div>
        <div className="inspectors-kpi-card">
          <span className="inspectors-kpi-value" style={{ color: "#f59e0b" }}>{counts.on_mission}</span>
          <span className="inspectors-kpi-label">En Mission</span>
        </div>
        <div className="inspectors-kpi-card">
          <span className="inspectors-kpi-value" style={{ color: "#94a3b8" }}>{counts.inactive}</span>
          <span className="inspectors-kpi-label">Inactifs</span>
        </div>
      </div>

      {/* ── Filters & Search ── */}
      <div className="inspectors-toolbar">
        <div className="inspectors-filter-tabs">
          {[
            { key: "all",        label: "Tous" },
            { key: "active",     label: "Actifs" },
            { key: "on_mission", label: "En Mission" },
            { key: "inactive",   label: "Inactifs" },
          ].map(({ key, label }) => (
            <button
              key={key}
              className={`inspectors-filter-tab ${filter === key ? "inspectors-filter-tab-active" : ""}`}
              onClick={() => setFilter(key)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="inspectors-search-wrap">
          <svg className="inspectors-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            className="inspectors-search-input"
            type="text"
            placeholder="Rechercher par nom, région, spécialité…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* ── Card list ── */}
      {filtered.length === 0 ? (
        <div className="inspectors-empty">
          <span style={{ fontSize: "2.5rem" }}>🔍</span>
          <p>Aucun inspecteur ne correspond à votre recherche.</p>
        </div>
      ) : (
        <div className="inspectors-list">
          {filtered.map((inspector) => (
            <InspectorCard key={inspector.id} inspector={inspector} />
          ))}
        </div>
      )}
    </div>
  );
}
