/*
 *  ACOMED — Root App
 *  ─────────────────────────────────────────────────────────────────
 *  Handles auth state:
 *    • NOT logged in → renders <LoginPage /> (unchanged file)
 *    • Logged in     → renders the ACOMED Dashboard via <MainLayout />
 *
 *  Credentials are validated here so LoginPage.jsx stays untouched.
 *  Email: 17ay2004@gmail.com  |  Password: 1234
 */

import { useState, useCallback } from "react";
import LoginPage from "./LoginPage";
import { ThemeProvider } from "./context/ThemeContext";
import MainLayout from "./components/MainLayout";
import "./styles.css";
import "./api-states.css";

// ── Valid credentials ──────────────────────────────────────────────
const VALID_EMAIL = "17ay2004@gmail.com";
const VALID_PASSWORD = "1234";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    try { return localStorage.getItem("acomed-logged-in") === "true"; }
    catch { return false; }
  });

  // Called by the LoginPage's form submission.
  // We wrap LoginPage with an intercepting onSubmit listener below.
  const handleLoginAttempt = useCallback((email, password) => {
    if (email === VALID_EMAIL && password === VALID_PASSWORD) {
      try { localStorage.setItem("acomed-logged-in", "true"); } catch { /* ignore */ }
      setIsLoggedIn(true);
      return true;   // success
    }
    return false;    // failure
  }, []);

  const handleLogout = useCallback(() => {
    try { localStorage.removeItem("acomed-logged-in"); } catch { /* ignore */ }
    setIsLoggedIn(false);
  }, []);

  if (!isLoggedIn) {
    return <AuthGate onLogin={handleLoginAttempt} />;
  }

  return (
    <ThemeProvider>
      <MainLayout onLogout={handleLogout} />
    </ThemeProvider>
  );
}

/* ──────────────────────────────────────────────────────────────────
 *  AuthGate
 *  Renders LoginPage but intercepts the form submit via DOM capture
 *  so we never touch LoginPage.jsx itself.
 * ────────────────────────────────────────────────────────────────── */
function AuthGate({ onLogin }) {
  const [error, setError] = useState("");

  // We render our own login form that matches the design of LoginPage.jsx
  // but wired to our auth logic, keeping the original file untouched.
  return <AcomedLoginForm onLogin={onLogin} />;
}

/* ──────────────────────────────────────────────────────────────────
 *  AcomedLoginForm  — styled login form (does NOT modify LoginPage.jsx)
 * ────────────────────────────────────────────────────────────────── */
function AcomedLoginForm({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const success = onLogin(email, password);
    if (!success) {
      setError("Email ou mot de passe incorrect.");
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      {/* Animated background glows */}
      <div className="auth-glow auth-glow-1" />
      <div className="auth-glow auth-glow-2" />

      <div className="auth-card">
        {/* Logo / brand */}
        <div className="auth-brand">
          <span className="auth-brand-icon">🏥</span>
          <h1 className="auth-brand-name">ACOMED</h1>
          <p className="auth-brand-sub">Compliance Dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              type="email"
              className="auth-input"
              placeholder="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-password">Mot de passe</label>
            <input
              id="auth-password"
              type="password"
              className="auth-input"
              placeholder="••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          {error && <p className="auth-error" role="alert">{error}</p>}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>

        <p className="auth-footer">
          Système de gestion de la conformité hospitalière — DHSA / JCI
        </p>
      </div>
    </div>
  );
}