/*
 * ═══════════════════════════════════════════════════════════════════
 *  ACOMED — Static Mock Data & Constants
 * ═══════════════════════════════════════════════════════════════════
 */

export const CATEGORY_CONFIG = [
  { key: "securite_incendie",     label: "Sécurité Incendie",           labelShort: "Incendie",    icon: "🔥",  weight: 0.20 },
  { key: "lutte_infections",      label: "Lutte contre les Infections",  labelShort: "Infections",  icon: "🦠",  weight: 0.25 },
  { key: "gestion_medicaments",   label: "Gestion des Médicaments",      labelShort: "Médicaments", icon: "💊",  weight: 0.20 },
  { key: "maintenance_equipements",label: "Maintenance des Équipements", labelShort: "Équipements", icon: "🔧",  weight: 0.15 },
  { key: "batiment_securite",     label: "Bâtiment et Sécurité",         labelShort: "Bâtiment",    icon: "🏗️", weight: 0.20 },
];

export const NATIONAL_AVERAGE = {
  securite_incendie: 65,
  lutte_infections: 60,
  gestion_medicaments: 62,
  maintenance_equipements: 58,
  batiment_securite: 64,
  global: 61.9,
};

export const ACCREDITATION_LEVELS = [
  { level: 1, label: "Niveau 1 — Normes de Base",        color: "#ef4444", min: 0,     max: 49.99 },
  { level: 2, label: "Niveau 2 — Documentation",         color: "#f59e0b", min: 50,    max: 70    },
  { level: 3, label: "Niveau 3 — Données et Résultats",  color: "#3b82f6", min: 70.01, max: 85    },
  { level: 4, label: "Niveau 4 — Amélioration Continue", color: "#10b981", min: 85.01, max: 100   },
];

export const HOSPITALS = [
  {
    id: 1,
    name: "Hôpital Régional Hassan II",
    type: "Hôpital Régional",
    city: "Agadir",
    region: "Souss-Massa",
    beds: 640,
    established: 1982,
    lastAudit: "2024-11-15",
    auditor: "Dr. Amina Benchekroun",
    service: "Urgences",
    globalScore: 78.55,
    accreditationLevel: 3,
    accreditationLabel: "Niveau 3 — Données et Résultats",
    totalIncidents: 3,
    criticalIncidents: 1,
    scores: { securite_incendie: 82, lutte_infections: 75, gestion_medicaments: 78, maintenance_equipements: 72, batiment_securite: 85 },
    pinPosition: { x: "52%", y: "30%" },
  },
  {
    id: 2,
    name: "Hôpital Préfectoral Inezgane",
    type: "Hôpital Préfectoral",
    city: "Inezgane",
    region: "Souss-Massa",
    beds: 280,
    established: 1995,
    lastAudit: "2024-10-22",
    auditor: "Dr. Youssef El Alaoui",
    service: "Bloc Opératoire",
    globalScore: 61.15,
    accreditationLevel: 2,
    accreditationLabel: "Niveau 2 — Documentation",
    totalIncidents: 5,
    criticalIncidents: 3,
    scores: { securite_incendie: 60, lutte_infections: 55, gestion_medicaments: 68, maintenance_equipements: 52, batiment_securite: 70 },
    pinPosition: { x: "72%", y: "66%" },
  },
  {
    id: 3,
    name: "Polyclinique CNSS Agadir",
    type: "Polyclinique",
    city: "Agadir",
    region: "Souss-Massa",
    beds: 150,
    established: 2005,
    lastAudit: "2024-12-03",
    auditor: "Dr. Fatima-Zahra Tazi",
    service: "Pédiatrie",
    globalScore: 88.7,
    accreditationLevel: 4,
    accreditationLabel: "Niveau 4 — Amélioration Continue",
    totalIncidents: 1,
    criticalIncidents: 0,
    scores: { securite_incendie: 90, lutte_infections: 92, gestion_medicaments: 85, maintenance_equipements: 82, batiment_securite: 92 },
    pinPosition: { x: "34%", y: "50%" },
  },
];

export function getAccreditationColor(level) {
  const acc = ACCREDITATION_LEVELS.find((a) => a.level === level);
  return acc ? acc.color : "#6b7280";
}

export function getScoreColor(score) {
  if (score >= 85) return "#10b981";
  if (score >= 70) return "#3b82f6";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

export function getScoreLabel(score) {
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Bon";
  if (score >= 50) return "Moyen";
  return "Insuffisant";
}
