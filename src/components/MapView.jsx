import { useState, useCallback } from "react";
import { HOSPITALS, getScoreColor, getAccreditationColor } from "../data/hospitalData";

// `hospitals` prop = live API data; falls back to static mock when not provided
export default function MapView({ hospitals, onSelectHospital }) {
  const displayHospitals = hospitals && hospitals.length > 0 ? hospitals : HOSPITALS;
  const [hoveredId, setHoveredId] = useState(null);

  const handlePinClick = useCallback(
    (hospital) => onSelectHospital(hospital),
    [onSelectHospital]
  );

  return (
    <div className="map-view">
      <div className="map-header">
        <h1 className="map-title">Carte des Hôpitaux — Agadir</h1>
        <p className="map-subtitle">
          Sélectionnez un établissement pour consulter son rapport de conformité
        </p>
      </div>

      <div className="map-wrapper">
        <div className="map-container">
          <svg className="map-svg" viewBox="0 0 1000 650" preserveAspectRatio="xMidYMid meet">
            <defs>
              <linearGradient id="oceanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1e40af" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0.10" />
              </linearGradient>
              <linearGradient id="beachGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.12" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.04" />
              </linearGradient>
            </defs>

            {/* Ocean */}
            <path d="M0,0 L370,0 Q330,120 290,260 Q260,380 290,490 Q310,570 360,650 L0,650 Z" className="map-ocean" fill="url(#oceanGradient)" />

            {/* Beach strip */}
            <path d="M370,0 Q330,120 290,260 Q260,380 290,490 Q310,570 360,650 L400,650 Q340,570 320,490 Q290,380 320,260 Q350,120 400,0 Z" fill="url(#beachGradient)" />

            {/* Coastline */}
            <path d="M370,0 Q330,120 290,260 Q260,380 290,490 Q310,570 360,650" className="map-coastline" />

            {/* Roads */}
            <line x1="380" y1="120" x2="980" y2="120" className="map-highway" />
            <text x="960" y="112" className="map-road-label">N1</text>
            <line x1="480" y1="120" x2="750" y2="500" className="map-highway" />
            <text x="755" y="495" className="map-road-label">N8</text>
            <line x1="370" y1="310" x2="900" y2="310" className="map-road" />
            <line x1="520" y1="0" x2="520" y2="650" className="map-road" />
            <line x1="680" y1="120" x2="680" y2="650" className="map-road" />
            <line x1="370" y1="480" x2="900" y2="480" className="map-road" />

            {/* Zones */}
            <circle cx="520" cy="210" r="90" className="map-zone" />
            <text x="520" y="215" className="map-zone-label">Agadir Centre</text>
            <circle cx="720" cy="440" r="75" className="map-zone" />
            <text x="720" y="445" className="map-zone-label">Inezgane</text>
            <circle cx="380" cy="370" r="60" className="map-zone" />
            <text x="380" y="375" className="map-zone-label">Anza</text>
            <circle cx="620" cy="160" r="50" className="map-zone" />
            <text x="620" y="165" className="map-zone-label">Hay Mohammadi</text>

            {/* Port */}
            <rect x="340" y="220" width="50" height="40" rx="4" className="map-port" />
            <text x="365" y="245" className="map-zone-label" fontSize="9">Port</text>

            {/* Compass */}
            <g transform="translate(920, 580)">
              <circle r="22" className="map-compass-bg" />
              <text y="-8" className="map-compass-letter">N</text>
              <line x1="0" y1="-5" x2="0" y2="5" className="map-compass-line" />
              <line x1="-5" y1="0" x2="5" y2="0" className="map-compass-line" />
              <polygon points="0,-16 -4,-8 4,-8" className="map-compass-arrow" />
            </g>

            {/* Ocean label */}
            <text x="140" y="350" className="map-ocean-label" transform="rotate(-75, 140, 350)">
              Océan Atlantique
            </text>
          </svg>

          {/* Hospital pins */}
          {displayHospitals.map((hospital) => (
            <div
              key={hospital.id}
              className="map-pin-wrapper"
              style={{ left: hospital.pinPosition.x, top: hospital.pinPosition.y }}
              onMouseEnter={() => setHoveredId(hospital.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => handlePinClick(hospital)}
              role="button"
              tabIndex={0}
              aria-label={`Voir les détails de ${hospital.name}`}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handlePinClick(hospital); }}
            >
              <span className="map-pin-pulse" />
              <span className="map-pin-pulse map-pin-pulse-delayed" />

              <svg className="map-pin-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z" />
              </svg>

              <span className="map-pin-name">{hospital.name}</span>

              <div className={`map-pin-card ${hoveredId === hospital.id ? "map-pin-card-visible" : ""}`}>
                <div className="map-pin-card-arrow" />
                <span className="map-pin-card-type">{hospital.type}</span>
                <span className="map-pin-card-hospital">{hospital.name}</span>
                <div className="map-pin-card-score-row">
                  <span className="map-pin-card-score" style={{ color: getScoreColor(hospital.globalScore) }}>
                    {hospital.globalScore}%
                  </span>
                  <span className="map-pin-card-badge" style={{ backgroundColor: getAccreditationColor(hospital.accreditationLevel) }}>
                    Niv. {hospital.accreditationLevel}
                  </span>
                </div>
                <span className="map-pin-card-cta">Cliquez pour les détails →</span>
              </div>
            </div>
          ))}
        </div>

        <div className="map-legend">
          <span className="map-legend-title">Légende</span>
          <div className="map-legend-item"><span className="map-legend-dot map-legend-dot-green" /><span>Score ≥ 85%</span></div>
          <div className="map-legend-item"><span className="map-legend-dot map-legend-dot-blue" /><span>Score 70–84%</span></div>
          <div className="map-legend-item"><span className="map-legend-dot map-legend-dot-amber" /><span>Score 50–69%</span></div>
          <div className="map-legend-item"><span className="map-legend-dot map-legend-dot-red" /><span>Score &lt; 50%</span></div>
        </div>
      </div>
    </div>
  );
}
