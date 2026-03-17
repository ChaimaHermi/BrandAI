// ==============================================================
//  frontend/src/pages/Login.jsx
//  RÔLE : Page de connexion connectée au vrai backend
//
//  VALIDATION CÔTÉ CLIENT (on blur) :
//    - email : format email valide (regex)
//    - password : non vide
//
//  GESTION D'ERREURS 401 (backend) :
//    - Si message contient "mot de passe" → "Mot de passe incorrect. Veuillez réessayer."
//    - Si message contient "Email" → sous le champ email : "Aucun compte trouvé avec cet email. Veuillez vous inscrire."
//      + lien cliquable "Pas encore de compte ? S'inscrire →" vers /register
//
//  FEEDBACK VISUEL :
//    - Champ valide → bordure verte + icône check
//    - Champ invalide → bordure rouge + icône X
//    - Toggle show/hide password
//    - Spinner dans le bouton pendant l'API call
// ==============================================================

import React, { useState, useRef } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  HiOutlineEnvelope,
  HiOutlineLockClosed,
  HiOutlineEye,
  HiOutlineEyeSlash,
  HiCheckCircle,
  HiXCircle,
} from "react-icons/hi2";
import { FcGoogle } from "react-icons/fc";
import { BlobBackground } from "../components/ui/BlobBackground";
import { Toast } from "../components/ui/Toast";
import { useAuth } from "../hooks/useAuth";
import { apiLogin } from "../services/authApi";

// ── Validateurs (exécutés on blur) ─────────────────────────────
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const validateEmail = (value) => {
  if (!value.trim()) return "";
  if (!EMAIL_REGEX.test(value.trim())) return "Veuillez entrer une adresse email valide.";
  return "";
};

const validatePassword = (value) => {
  if (!value.trim()) return "Le mot de passe ne peut pas être vide.";
  return "";
};

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [touched, setTouched] = useState({ email: false, password: false });

  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const pendingAuthData = useRef(null);

  const handleGoogleLogin = () => {
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
    window.location.href = `${API_URL}/auth/google`;
  };

  const handleBlur = (field) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  const displayEmailError = touched.email ? validateEmail(email) : "";
  const displayPasswordError = touched.password ? validatePassword(password) : "";

  const isFormValid =
    !displayEmailError &&
    !displayPasswordError &&
    EMAIL_REGEX.test(email.trim()) &&
    password.trim().length > 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setEmailError("");
    setPasswordError("");
    setLoading(true);

    try {
      const data = await apiLogin({ email, password });
      pendingAuthData.current = data;

      setToastMessage(`Connexion réussie ! Bon retour, ${data.user?.name || "!"}`);
      setShowToast(true);
    } catch (err) {
      const msg = err.message || "";
      const status = err.status;

      if (status === 401) {
        if (msg.toLowerCase().includes("mot de passe")) {
          setError("Mot de passe incorrect. Veuillez réessayer.");
          setEmailError("");
          setPasswordError("");
        } else if (msg.toLowerCase().includes("email")) {
          setError("");
          setEmailError("Aucun compte trouvé avec cet email. Veuillez vous inscrire.");
          setPasswordError("");
        } else {
          setError(msg);
        }
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const inputBase =
    "w-full h-10 rounded-lg border bg-white pl-10 text-sm text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-1 ";
  const inputValid = "border-green-400 focus:border-green-500 focus:ring-green-500";
  const inputInvalid = "border-red-400 focus:border-red-500 focus:ring-red-500";
  const inputNeutral = "border-[#E5E7EB] focus:border-[#7C3AED] focus:ring-[#7C3AED]";

  const getInputClass = (hasError, hasValue, touchedField, hasToggle = false) => {
    let base = inputBase + (hasToggle ? "pr-20" : "pr-12");
    if (!touchedField) return base + " " + inputNeutral;
    if (hasError) return base + " " + inputInvalid;
    if (hasValue && !hasError) return base + " " + inputValid;
    return base + " " + inputNeutral;
  };

  const FieldIcon = ({ error, touched, value }) => {
    if (!touched || (!value && !error)) return null;
    if (error) return <HiXCircle className="h-5 w-5 text-red-500" />;
    return <HiCheckCircle className="h-5 w-5 text-green-500" />;
  };

  const effectiveEmailError = emailError || displayEmailError;
  const effectivePasswordError = passwordError || displayPasswordError;

  return (
    <div className="relative h-screen flex items-center justify-center bg-gray-50 overflow-hidden">
      <Toast
        message={toastMessage}
        visible={showToast}
        onClose={() => {
          if (pendingAuthData.current) {
            login(pendingAuthData.current);
            pendingAuthData.current = null;
          }
          navigate("/dashboard", { replace: true });
        }}
        duration={2000}
      />
      <BlobBackground opacity={0.2} className="pointer-events-none absolute inset-0 z-0" />

      <div className="relative z-10 w-full max-w-[420px] mx-4">
        <div className="w-full max-w-[420px] bg-white rounded-xl border border-[#E5E7EB] shadow-sm p-6 space-y-5">
          <div className="flex flex-col items-center gap-2 mb-2">
            <img
              src="/logo%20brand%20ai.png"
              alt="BrandAI"
              className="h-12 w-auto"
            />
            <h1 className="text-xl font-semibold text-[#111827]">
              Bienvenue sur BrandAI
            </h1>
            <p className="text-sm text-[#6B7280]">Connectez-vous pour continuer</p>
          </div>

          {(searchParams.get("error") === "google_failed" || searchParams.get("error") === "google_auth_failed") && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-600">
              Connexion Google échouée. Veuillez réessayer.
            </div>
          )}

          <button
            type="button"
            onClick={handleGoogleLogin}
            className="w-full h-11 flex items-center justify-center gap-2 border border-[#E5E7EB] rounded-lg bg-white font-medium text-[#111827] hover:bg-gray-50 transition"
          >
            <FcGoogle className="h-5 w-5" /> Continuer avec Google
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#E5E7EB]" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-sm text-[#6B7280]">— ou —</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
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
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setEmailError("");
                  }}
                  onBlur={() => handleBlur("email")}
                  placeholder="vous@exemple.com"
                  className={getInputClass(!!effectiveEmailError, !!email.trim(), touched.email, false)}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2">
                  <FieldIcon error={effectiveEmailError} touched={touched.email} value={email.trim()} />
                </span>
              </div>
              {effectiveEmailError && (
                <p className="mt-1 text-xs text-red-500">
                  {effectiveEmailError}
                  {emailError && (
                    <>
                      {" "}
                      <Link
                        to="/register"
                        className="font-medium text-[#7C3AED] hover:underline"
                      >
                        Pas encore de compte ? S&apos;inscrire →
                      </Link>
                    </>
                  )}
                </p>
              )}
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
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setPasswordError("");
                  }}
                  onBlur={() => handleBlur("password")}
                  placeholder="••••••••"
                  className={getInputClass(!!effectivePasswordError, !!password, touched.password, true)}
                />
                <span className="absolute right-10 top-1/2 flex -translate-y-1/2 items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-[#6B7280] hover:text-[#111827]"
                    aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                  >
                    {showPassword ? <HiOutlineEyeSlash className="h-5 w-5" /> : <HiOutlineEye className="h-5 w-5" />}
                  </button>
                  <FieldIcon error={effectivePasswordError} touched={touched.password} value={password} />
                </span>
              </div>
              {effectivePasswordError && (
                <p className="mt-1 text-xs text-red-500">{effectivePasswordError}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={!isFormValid || loading}
              className="w-full h-11 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                "Se connecter"
              )}
            </button>
          </form>

          <p className="pt-2 text-center text-sm text-[#6B7280]">
            Pas encore de compte ?{" "}
            <Link
              to="/register"
              className="font-medium text-[#7C3AED] hover:underline"
            >
              S&apos;inscrire
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
