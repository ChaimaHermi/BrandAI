// ==============================================================
//  frontend/src/context/AuthContext.jsx
//  RÔLE : Gérer l'état d'authentification global
//
//  POURQUOI UN CONTEXT ?
//    Sans Context, chaque composant devrait lire localStorage
//    séparément → duplication + incohérence.
//    Avec Context → un seul endroit qui gère l'état,
//    tous les composants y ont accès via useAuth()
//
//  CE QUE CE CONTEXT STOCKE :
//    user  → { id, name, email }
//    token → le JWT (envoyé dans Authorization: Bearer <token>)
//
//  PERSISTANCE :
//    localStorage → l'utilisateur reste connecté après refresh de page
//    Si pas de localStorage → déconnecté au refresh
//
//  UTILISATION DANS UN COMPOSANT :
//    import { useAuth } from "../hooks/useAuth"
//    const { user, token, login, logout, isAuthenticated } = useAuth()
// ==============================================================

import React, { createContext, useContext, useState, useEffect } from "react";

// Clés de stockage dans localStorage
const TOKEN_KEY = "brandai_token";
const USER_KEY = "brandai_user";

// Le contexte — null par défaut (détecte si utilisé hors Provider)
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  // ── Restaurer la session au démarrage ────────────────────────
  // Au chargement de l'app, on vérifie si un token existe en localStorage
  // Si oui → on recharge user et token → l'utilisateur reste connecté
  // Si non → user = null → redirigé vers /login par ProtectedRoute
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch {
        // JSON corrompu dans localStorage → on nettoie tout
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
  }, []); // [] → s'exécute une seule fois au montage du composant

  // ── login() ──────────────────────────────────────────────────
  // Appelé après apiRegister() ou apiLogin() réussi.
  // Reçoit la réponse du backend :
  // { access_token: "eyJ...", user: { id, name, email } }
  const login = ({ access_token, user: userData }) => {
    setToken(access_token);
    setUser(userData);
    // Persistance : survit au refresh de page
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
  };

  // ── logout() ─────────────────────────────────────────────────
  // Appelé quand l'utilisateur clique sur "Déconnexion"
  // Vide l'état ET localStorage
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    // ProtectedRoute redirigera automatiquement vers /login
  };

  // Valeur exposée à tous les composants enfants
  const value = {
    user, // { id, name, email } ou null
    token, // "eyJhbGci..." ou null
    login, // fonction : appelée après register/login réussi
    logout, // fonction : appelée au clic sur "Déconnexion"
    isAuthenticated: !!user && !!token, // true si connecté
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook interne — utilisé par useAuth.js
export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuthContext doit être utilisé dans AuthProvider");
  }
  return ctx;
}

export default AuthContext;
