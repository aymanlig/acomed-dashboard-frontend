import { useCallback } from "react";
import { useTheme } from "../context/ThemeContext";

function IconGrid() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

function IconBookmark() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
    </svg>
  );
}

function IconClock() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 3" />
    </svg>
  );
}

function IconLogout() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  );
}

function IconUserBadge() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <circle cx="9" cy="10" r="2.5" />
      <path d="M4 20c0-2 2-3.5 5-3.5s5 1.5 5 3.5" />
      <line x1="15" y1="9" x2="20" y2="9" />
      <line x1="15" y1="13" x2="18" y2="13" />
    </svg>
  );
}

function IconSun() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </svg>
  );
}

function IconMoon() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
    </svg>
  );
}

function IconClose() {
  return (
    <svg className="sidebar-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

const NAV_ITEMS = [
  { id: "dashboard",  label: "Tableau de Bord",      Icon: IconGrid      },
  { id: "watchlist",  label: "Hôpitaux Sauvegardés", Icon: IconBookmark  },
  { id: "history",    label: "Historique",            Icon: IconClock     },
  { id: "inspectors", label: "Inspecteurs",           Icon: IconUserBadge },
];

export default function Sidebar({ isOpen, onClose, activePage, onNavigate, onLogout }) {
  const { darkMode, toggleTheme } = useTheme();

  const handleNavClick = useCallback(
    (pageId) => { onNavigate(pageId); onClose(); },
    [onNavigate, onClose]
  );

  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={onClose} aria-hidden="true" />}

      <aside className={`sidebar-container ${isOpen ? "sidebar-open" : ""}`} aria-label="Main navigation">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <span className="sidebar-brand-logo">🏥</span>
            <div className="sidebar-brand-text">
              <span className="sidebar-brand-name">ACOMED</span>
              <span className="sidebar-brand-sub">Compliance Dashboard</span>
            </div>
          </div>
          <button className="sidebar-close-btn" onClick={onClose} aria-label="Close sidebar">
            <IconClose />
          </button>
        </div>

        <div className="sidebar-divider" />

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ id, label, Icon }) => (
            <button
              key={id}
              className={`sidebar-nav-item ${activePage === id ? "sidebar-nav-item-active" : ""}`}
              onClick={() => handleNavClick(id)}
            >
              <Icon />
              <span className="sidebar-nav-label">{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-divider" />

        <button className="sidebar-theme-toggle" onClick={toggleTheme}>
          {darkMode ? <IconSun /> : <IconMoon />}
          <span className="sidebar-nav-label">{darkMode ? "Mode Clair" : "Mode Sombre"}</span>
          <span className="sidebar-theme-badge">{darkMode ? "☀️" : "🌙"}</span>
        </button>

        <div className="sidebar-spacer" />
        <div className="sidebar-divider" />

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">A</div>
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">Dr. Admin</span>
              <span className="sidebar-user-role">Administrateur</span>
            </div>
          </div>
          <button className="sidebar-logout-btn" onClick={onLogout}>
            <IconLogout />
            <span className="sidebar-nav-label">Déconnexion</span>
          </button>
        </div>
      </aside>
    </>
  );
}
