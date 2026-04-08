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
import { BlobBackground } from "@/components/ui/BlobBackground";
import { Toast } from "@/shared/ui/Toast";
import { useAuth } from "@/shared/hooks/useAuth";
import { apiLogin } from "@/services/authApi";

/* ── Validation (logic unchanged) ─────────────────────────────────────── */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const validateEmail    = (v) => !v.trim() ? "" : !EMAIL_REGEX.test(v.trim()) ? "Adresse email invalide." : "";
const validatePassword = (v) => !v.trim() ? "Le mot de passe ne peut pas être vide." : "";

/* ── Input field classes ───────────────────────────────────────────────── */
const inputBase    = "w-full h-11 rounded-xl border bg-white pl-11 text-base text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-2 transition-all duration-150 ";
const inputNeutral = "border-gray-200 focus:border-brand focus:ring-brand/20";
const inputValid   = "border-success focus:border-success focus:ring-success/20";
const inputInvalid = "border-red-400 focus:border-red-400 focus:ring-red-400/20";

function getInputClass(hasError, hasValue, touched, hasToggle = false) {
  const pr = hasToggle ? "pr-20" : "pr-11";
  if (!touched) return `${inputBase} ${pr} ${inputNeutral}`;
  if (hasError)  return `${inputBase} ${pr} ${inputInvalid}`;
  if (hasValue)  return `${inputBase} ${pr} ${inputValid}`;
  return `${inputBase} ${pr} ${inputNeutral}`;
}

function FieldIcon({ error, touched, value }) {
  if (!touched || (!value && !error)) return null;
  if (error) return <HiXCircle className="h-5 w-5 text-red-500" />;
  return <HiCheckCircle className="h-5 w-5 text-success" />;
}

/* ── Component ─────────────────────────────────────────────────────────── */
export function Login() {
  const [email, setEmail]           = useState("");
  const [password, setPassword]     = useState("");
  const [error, setError]           = useState("");
  const [emailError, setEmailError] = useState("");
  const [loading, setLoading]       = useState(false);
  const [showPassword, setShowPwd]  = useState(false);
  const [showToast, setShowToast]   = useState(false);
  const [toastMessage, setToastMsg] = useState("");
  const [touched, setTouched]       = useState({ email: false, password: false });

  const { login }        = useAuth();
  const navigate         = useNavigate();
  const [searchParams]   = useSearchParams();
  const pendingAuth      = useRef(null);

  const handleGoogleLogin = () => {
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
    window.location.href = `${API_URL}/auth/google`;
  };

  const handleBlur = (field) => setTouched((p) => ({ ...p, [field]: true }));

  const displayEmailError    = touched.email    ? validateEmail(email)       : "";
  const displayPasswordError = touched.password ? validatePassword(password) : "";
  const effectiveEmailError  = emailError || displayEmailError;

  const isFormValid =
    !displayEmailError && !displayPasswordError &&
    EMAIL_REGEX.test(email.trim()) && password.trim().length > 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setEmailError(""); setLoading(true);
    try {
      const data = await apiLogin({ email, password });
      pendingAuth.current = data;
      setToastMsg(`Connexion réussie ! Bon retour, ${data.user?.name || "!"}`);
      setShowToast(true);
    } catch (err) {
      const msg    = err.message || "";
      const status = err.status;
      if (status === 401) {
        if (msg.toLowerCase().includes("mot de passe"))
          setError("Mot de passe incorrect. Veuillez réessayer.");
        else if (msg.toLowerCase().includes("email"))
          setEmailError("Aucun compte trouvé avec cet email.");
        else setError(msg);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-brand-50">
      <Toast
        message={toastMessage}
        visible={showToast}
        onClose={() => {
          if (pendingAuth.current) { login(pendingAuth.current); pendingAuth.current = null; }
          navigate("/dashboard", { replace: true });
        }}
        duration={2000}
      />
      <BlobBackground opacity={0.15} className="pointer-events-none absolute inset-0 z-0" />

      <div className="relative z-10 mx-4 w-full max-w-md">
        {/* Card */}
        <div className="rounded-2xl border border-brand-border bg-white p-8 shadow-card-md space-y-6">

          {/* Header */}
          <div className="flex flex-col items-center gap-2 text-center">
            <img src="/logo%20brand%20ai.png" alt="BrandAI" className="h-12 w-auto" />
            <h1 className="text-2xl font-extrabold text-ink">Bienvenue sur BrandAI</h1>
            <p className="text-sm text-ink-muted">Connectez-vous pour continuer</p>
          </div>

          {/* Google error */}
          {(searchParams.get("error") === "google_failed" ||
            searchParams.get("error") === "google_auth_failed") && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              Connexion Google échouée. Veuillez réessayer.
            </div>
          )}

          {/* Google SSO */}
          <button
            type="button"
            onClick={handleGoogleLogin}
            className="flex h-11 w-full items-center justify-center gap-2.5 rounded-xl border border-gray-200 bg-white text-sm font-semibold text-ink transition-all hover:border-brand-muted hover:bg-brand-50"
          >
            <FcGoogle className="h-5 w-5" />
            Continuer avec Google
          </button>

          {/* Divider */}
          <div className="relative flex items-center gap-3">
            <div className="flex-1 border-t border-gray-100" />
            <span className="text-xs text-ink-subtle">ou</span>
            <div className="flex-1 border-t border-gray-100" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Email */}
            <div>
              <label htmlFor="login-email" className="mb-1.5 block text-sm font-semibold text-ink">
                Email
              </label>
              <div className="relative">
                <HiOutlineEnvelope className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-subtle" />
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setEmailError(""); }}
                  onBlur={() => handleBlur("email")}
                  placeholder="vous@exemple.com"
                  className={getInputClass(!!effectiveEmailError, !!email.trim(), touched.email)}
                />
                <span className="absolute right-3.5 top-1/2 -translate-y-1/2">
                  <FieldIcon error={effectiveEmailError} touched={touched.email} value={email.trim()} />
                </span>
              </div>
              {effectiveEmailError && (
                <p className="mt-1.5 text-xs text-red-500">
                  {effectiveEmailError}
                  {emailError && (
                    <> <Link to="/register" className="font-semibold text-brand hover:underline">S&apos;inscrire →</Link></>
                  )}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-sm font-semibold text-ink">
                Mot de passe
              </label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-subtle" />
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => handleBlur("password")}
                  placeholder="••••••••"
                  className={getInputClass(!!displayPasswordError, !!password, touched.password, true)}
                />
                <span className="absolute right-3.5 top-1/2 flex -translate-y-1/2 items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setShowPwd((v) => !v)}
                    className="text-ink-subtle hover:text-ink"
                    aria-label={showPassword ? "Masquer" : "Afficher"}
                  >
                    {showPassword ? <HiOutlineEyeSlash className="h-5 w-5" /> : <HiOutlineEye className="h-5 w-5" />}
                  </button>
                  <FieldIcon error={displayPasswordError} touched={touched.password} value={password} />
                </span>
              </div>
              {displayPasswordError && (
                <p className="mt-1.5 text-xs text-red-500">{displayPasswordError}</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={!isFormValid || loading}
              className="flex h-11 w-full items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-sm font-bold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading
                ? <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                : "Se connecter"}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-sm text-ink-muted">
            Pas encore de compte ?{" "}
            <Link to="/register" className="font-semibold text-brand hover:underline">
              S&apos;inscrire
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
