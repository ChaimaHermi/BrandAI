// ==============================================================
//  frontend/src/pages/GoogleCallback.jsx
//  RÔLE : Page intermédiaire après redirection Google OAuth
//
//  FLUX :
//    1. Lit le token JWT depuis ?token=... dans l'URL
//    2. Appelle apiGetMe(token) pour récupérer les infos utilisateur
//    3. Appelle login({ access_token, user }) pour stocker la session
//    4. Redirige vers /dashboard en cas de succès
//    5. Redirige vers /login?error=google_failed en cas d'erreur
// ==============================================================

import React, { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";
import { apiGetMe } from "@/services/authApi";

export function GoogleCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();

  useEffect(() => {
    const token = searchParams.get("token");

    const processCallback = async () => {
      if (!token) {
        navigate("/login?error=google_failed", { replace: true });
        return;
      }

      try {
        const user = await apiGetMe(token);
        login({ access_token: token, user });
        navigate("/dashboard", { replace: true });
      } catch {
        navigate("/login?error=google_failed", { replace: true });
      }
    };

    processCallback();
  }, [searchParams, login, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-white">
      <div className="flex flex-col items-center gap-4">
        <span
          className="h-10 w-10 animate-spin rounded-full border-4 border-[#E5E7EB] border-t-[#7C3AED]"
          aria-hidden="true"
        />
        <p className="text-sm text-[#6B7280]">Connexion en cours...</p>
      </div>
    </div>
  );
}

export default GoogleCallback;
