// ==============================================================
//  frontend/src/pages/Register.jsx
//  RÔLE : Page d'inscription connectée au vrai backend
//
//  FLUX COMPLET :
//    1. Utilisateur remplit name, email, password, confirm
//    2. Validation locale : password === confirm
//    3. handleSubmit() appelle apiRegister()
//    4. apiRegister() fait POST /api/auth/register
//    5. Backend crée l'user → retourne { access_token, user }
//    6. login() stocke dans AuthContext + localStorage
//    7. navigate("/dashboard") → redirigé
// ==============================================================

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HiOutlineUser,
  HiOutlineEnvelope,
  HiOutlineLockClosed,
} from "react-icons/hi2";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { BlobBackground } from "../components/ui/BlobBackground";
import { useAuth } from "../hooks/useAuth";
import { apiRegister } from "../services/authApi"; // ← vrai appel API

export function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  // Validation côté client avant d'envoyer au serveur
  const passwordsMatch = password === confirm;
  const isValid =
    name.trim() && email.trim() && password.length >= 6 && passwordsMatch;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid) return;

    setError("");
    setLoading(true);

    try {
      // ── Appel API ────────────────────────────────────────
      const data = await apiRegister({ name, email, password });

      // ── Stocker dans le Context ──────────────────────────
      login(data);

      // ── Rediriger ─────────────────────────────────────────
      navigate("/dashboard", { replace: true });
    } catch (err) {
      // Ex : "Un compte avec cet email existe déjà"
      setError(err.message);
    } finally {
      setLoading(false);
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
              Créer un compte
            </h1>
            <p className="mb-6 text-[#6B7280]">Rejoignez BrandAI</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Message d'erreur backend */}
            {error && (
              <div className="rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Nom */}
            <div>
              <label
                htmlFor="reg-name"
                className="mb-1.5 block text-sm font-medium text-[#111827]"
              >
                Nom complet
              </label>
              <div className="relative">
                <HiOutlineUser className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="reg-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ahmed Ben Ali"
                  required
                  className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="reg-email"
                className="mb-1.5 block text-sm font-medium text-[#111827]"
              >
                Email
              </label>
              <div className="relative">
                <HiOutlineEnvelope className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="reg-email"
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
                htmlFor="reg-password"
                className="mb-1.5 block text-sm font-medium text-[#111827]"
              >
                Mot de passe
              </label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="reg-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]"
                />
              </div>
              {password.length > 0 && password.length < 6 && (
                <p className="mt-1 text-xs text-red-500">
                  Minimum 6 caractères
                </p>
              )}
            </div>

            {/* Confirm password */}
            <div>
              <label
                htmlFor="reg-confirm"
                className="mb-1.5 block text-sm font-medium text-[#111827]"
              >
                Confirmer le mot de passe
              </label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="reg-confirm"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="••••••••"
                  required
                  className={`w-full rounded-[10px] border bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-1 ${
                    confirm.length > 0 && !passwordsMatch
                      ? "border-red-400 focus:border-red-400 focus:ring-red-400"
                      : "border-[#E5E7EB] focus:border-[#7C3AED] focus:ring-[#7C3AED]"
                  }`}
                />
              </div>
              {confirm.length > 0 && !passwordsMatch && (
                <p className="mt-1 text-xs text-red-500">
                  Les mots de passe ne correspondent pas
                </p>
              )}
            </div>

            {/* Bouton submit */}
            <Button
              type="submit"
              variant="primary"
              fullWidth
              disabled={!isValid || loading}
              className="py-3"
            >
              {loading ? (
                <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                "Créer mon compte"
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-[#6B7280]">
            Déjà un compte ?{" "}
            <Link
              to="/login"
              className="font-medium text-[#7C3AED] hover:underline"
            >
              Se connecter
            </Link>
          </p>
        </Card>
      </div>
    </div>
  );
}

export default Register;
