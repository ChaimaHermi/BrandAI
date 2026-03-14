// ==============================================================
//  frontend/src/services/authApi.js
//  RÔLE : Toutes les requêtes HTTP vers le backend
//         liées à l'authentification
//
//  RÈGLE : Les composants React ne font JAMAIS de fetch()
//          directement. Ils passent par ces fonctions.
//          → Si l'URL change, on change ici seulement
//          → Plus facile à tester et maintenir
//
//  ANALOGUE NODE.JS (client) :
//    // services/authService.js (côté frontend)
//    const register = async (data) => {
//      const res = await axios.post('/api/auth/register', data)
//      return res.data
//    }
// ==============================================================

// URL du backend lue depuis .env.local
// VITE_ est obligatoire pour que Vite l'expose dans le code
// Vite remplace import.meta.env.VITE_API_URL au moment du build
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// ==============================================================
//  UTILITAIRE INTERNE
// ==============================================================

/**
 * Parse la réponse fetch et lève une erreur si status >= 400
 * Le backend FastAPI renvoie toujours { "detail": "message" } pour les erreurs
 */
async function handleResponse(res) {
  const data = await res.json();
  if (!res.ok) {
    // FastAPI renvoie { "detail": "message d'erreur" }
    throw new Error(data.detail || "Une erreur est survenue");
  }
  return data;
}

// ==============================================================
//  FONCTIONS PUBLIQUES
// ==============================================================

/**
 * Inscription d'un nouvel utilisateur
 *
 * @param {{ name: string, email: string, password: string }} payload
 * @returns {Promise<{ access_token: string, token_type: string, user: object }>}
 *
 * UTILISATION DANS Register.jsx :
 *   const data = await apiRegister({ name, email, password })
 *   login(data) // stocke token + user dans AuthContext
 */
export async function apiRegister({ name, email, password }) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  return handleResponse(res);
}

/**
 * Connexion d'un utilisateur existant
 *
 * @param {{ email: string, password: string }} payload
 * @returns {Promise<{ access_token: string, token_type: string, user: object }>}
 *
 * UTILISATION DANS Login.jsx :
 *   const data = await apiLogin({ email, password })
 *   login(data)
 */
export async function apiLogin({ email, password }) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res);
}

/**
 * Récupère le profil de l'utilisateur connecté
 * Nécessite le token JWT dans le header
 *
 * @param {string} token - JWT stocké dans localStorage
 * @returns {Promise<{ id: number, name: string, email: string, created_at: string }>}
 *
 * UTILISATION (par ex pour vérifier si le token est encore valide) :
 *   const user = await apiGetMe(token)
 */
export async function apiGetMe(token) {
  const res = await fetch(`${API_URL}/auth/me`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      // Le backend lit ce header et vérifie le JWT
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse(res);
}
