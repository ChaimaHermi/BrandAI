// ==============================================================
//  frontend/src/pages/Login.jsx
//  RÔLE : Page de connexion connectée au vrai backend
//
//  FLUX COMPLET :
//    1. Utilisateur remplit email + password
//    2. handleSubmit() appelle apiLogin()
//    3. apiLogin() fait POST /api/auth/login
//    4. Backend vérifie → retourne { access_token, user }
//    5. login() stocke dans AuthContext + localStorage
//    6. navigate("/dashboard") → redirigé
//
//  GESTION D'ERREURS :
//    - Email/password incorrects → affiche le message du backend
//    - Réseau coupé → affiche "Une erreur est survenue"
//    - Loading state → désactive le bouton pendant la requête
// ==============================================================

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { HiOutlineEnvelope, HiOutlineLockClosed } from "react-icons/hi2";
import { FcGoogle } from "react-icons/fc";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { BlobBackground } from "../components/ui/BlobBackground";
import { useAuth } from "../hooks/useAuth";
import { apiLogin } from "../services/authApi"; // ← vrai appel API

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(""); // message d'erreur à afficher
  const [loading, setLoading] = useState(false); // désactive le bouton pendant requête

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); // reset l'erreur précédente
    setLoading(true);

    try {
      // ── Appel API ────────────────────────────────────────
      // apiLogin fait POST /api/auth/login
      // Retourne { access_token, token_type, user }
      // Lève une Error si le backend répond avec 4xx/5xx
      const data = await apiLogin({ email, password });

      // ── Stocker dans le Context ──────────────────────────
      // login() stocke user + token dans AuthContext + localStorage
      login(data);

      // ── Rediriger vers le dashboard ───────────────────────
      navigate("/dashboard", { replace: true });
    } catch (err) {
      // err.message contient le "detail" du backend
      // Ex : "Email ou mot de passe incorrect"
      setError(err.message);
    } finally {
      setLoading(false); // toujours réactiver le bouton
    }
  };

  return (
    <div className="relative min-h-screen bg-white">
      <BlobBackground opacity={0.35} className="pointer-events-none z-0" />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-12">
        <Card
          className="w-full max-w-[420px] shadow-[0_8px_32px_rgba(0,0,0,0.06)]"
          hover={false}
        >
          {/* Logo */}
          <div className="flex flex-col items-center text-center">
            <img
              src="/logo%20brand%20ai.png"
              alt="BrandAI"
              className="mb-4 h-14 w-auto"
            />
            <h1 className="mb-2 text-xl font-semibold text-[#111827]">
              Bienvenue sur BrandAI
            </h1>
            <p className="mb-6 text-[#6B7280]">Connectez-vous pour continuer</p>
          </div>

          {/* Google (désactivé pour l'instant) */}
          <button
            type="button"
            disabled
            className="mb-6 flex w-full cursor-not-allowed items-center justify-center gap-3 rounded-[10px] border border-[#E5E7EB] bg-[#F9FAFB] py-3 font-medium text-[#9CA3AF]"
          >
            <FcGoogle className="h-5 w-5" /> Continuer avec Google
            <span className="ml-1 text-xs">(bientôt)</span>
          </button>

          {/* Séparateur */}
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#E5E7EB]" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-sm text-[#6B7280]">ou</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Message d'erreur */}
            {error && (
              <div className="rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Email */}
            <div>
              <label
                htmlFor="login-email"
                className="mb-1.5 block text-sm font-medium text-[#111827]"
              >
                Email
              </label>
              <div className="relative">
                <HiOutlineEnvelope className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="vous@exemple.com"
                  required
                  className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="login-password"
                className="mb-1.5 block text-sm font-medium text-[#111827]"
              >
                Mot de passe
              </label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]"
                />
              </div>
            </div>

            {/* Bouton submit */}
            <Button
              type="submit"
              variant="primary"
              fullWidth
              disabled={!email || !password || loading}
              className="py-3"
            >
              {loading ? (
                <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                "Se connecter"
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-[#6B7280]">
            Pas encore de compte ?{" "}
            <Link
              to="/register"
              className="font-medium text-[#7C3AED] hover:underline"
            >
              S'inscrire
            </Link>
          </p>
        </Card>
      </div>
    </div>
  );
}

export default Login;
