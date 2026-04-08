import React, { useState, useRef } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  HiOutlineUser,
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
import { apiRegister } from "@/services/authApi";

/* ── Validation (logic unchanged) ─────────────────────────────────────── */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const validateNameField = (v, label) => {
  if (!v.trim()) return "";
  if (v.trim().length < 2) return `Le ${label} doit contenir au moins 2 caractères.`;
  if (/\d/.test(v)) return `Le ${label} ne doit pas contenir de chiffres.`;
  return "";
};
const validateEmail    = (v) => !v.trim() ? "" : !EMAIL_REGEX.test(v.trim()) ? "Adresse email invalide." : "";
const validatePassword = (v) => {
  if (!v) return "";
  if (v.length < 6)    return "Au moins 6 caractères.";
  if (!/[A-Z]/.test(v)) return "Au moins une majuscule.";
  if (!/\d/.test(v))    return "Au moins un chiffre.";
  return "";
};
const validateConfirm = (c, p) => !c ? "" : c !== p ? "Les mots de passe ne correspondent pas." : "";

function getPasswordStrength(pwd) {
  if (!pwd) return { level: 0, label: "", color: "" };
  let met = 0;
  if (pwd.length >= 6)    met++;
  if (/[A-Z]/.test(pwd)) met++;
  if (/\d/.test(pwd))    met++;
  if (met === 1) return { level: 1, label: "Faible", color: "bg-red-500" };
  if (met === 2) return { level: 2, label: "Moyen",  color: "bg-amber-500" };
  return              { level: 3, label: "Fort",   color: "bg-success" };
}

/* ── Input field classes ───────────────────────────────────────────────── */
const inputBase    = "w-full h-11 rounded-xl border bg-white pl-11 text-base text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-2 transition-all duration-150 ";
const inputNeutral = "border-gray-200 focus:border-brand focus:ring-brand/20";
const inputValid   = "border-success focus:border-success focus:ring-success/20";
const inputInvalid = "border-red-400 focus:border-red-400 focus:ring-red-400/20";

function getInputClass(hasError, hasValue, touched, hasToggle = false) {
  const pr = hasToggle ? "pr-20" : "pr-11";
  if (!touched) return `${inputBase} ${pr} ${inputNeutral}`;
  if (hasError) return `${inputBase} ${pr} ${inputInvalid}`;
  if (hasValue) return `${inputBase} ${pr} ${inputValid}`;
  return `${inputBase} ${pr} ${inputNeutral}`;
}

function FieldIcon({ error, touched, value }) {
  if (!touched || (!value && !error)) return null;
  if (error) return <HiXCircle className="h-5 w-5 text-red-500" />;
  return <HiCheckCircle className="h-5 w-5 text-success" />;
}

/* ── Component ─────────────────────────────────────────────────────────── */
export default function RegisterPage() {
  const [prenom, setPrenom]             = useState("");
  const [nom, setNom]                   = useState("");
  const [email, setEmail]               = useState("");
  const [password, setPassword]         = useState("");
  const [confirm, setConfirm]           = useState("");
  const [error, setError]               = useState("");
  const [loading, setLoading]           = useState(false);
  const [showPassword, setShowPwd]      = useState(false);
  const [showConfirm, setShowConfirm]   = useState(false);
  const [showToast, setShowToast]       = useState(false);
  const [toastMessage, setToastMsg]     = useState("");
  const [touched, setTouched]           = useState({
    prenom: false, nom: false, email: false, password: false, confirm: false,
  });

  const { login }      = useAuth();
  const navigate       = useNavigate();
  const [searchParams] = useSearchParams();
  const pendingAuth    = useRef(null);

  const handleGoogleLogin = () => {
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
    window.location.href = `${API_URL}/auth/google`;
  };
  const handleBlur = (field) => setTouched((p) => ({ ...p, [field]: true }));

  const prenomError   = touched.prenom   ? validateNameField(prenom, "prénom") : "";
  const nomError      = touched.nom      ? validateNameField(nom, "nom")       : "";
  const emailError    = touched.email    ? validateEmail(email)                : "";
  const passwordError = touched.password ? validatePassword(password)          : "";
  const confirmError  = touched.confirm  ? validateConfirm(confirm, password)  : "";
  const passwordStrength = getPasswordStrength(password);
  const fullName = `${prenom.trim()} ${nom.trim()}`.trim();

  const isFormValid =
    !prenomError && !nomError && !emailError && !passwordError && !confirmError &&
    prenom.trim().length >= 2 && !/\d/.test(prenom) &&
    nom.trim().length >= 2   && !/\d/.test(nom) &&
    EMAIL_REGEX.test(email.trim()) &&
    password.length >= 6 && /[A-Z]/.test(password) && /\d/.test(password) &&
    confirm === password;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isFormValid) return;
    setError(""); setLoading(true);
    try {
      const data = await apiRegister({ name: fullName, email, password });
      pendingAuth.current = data;
      setToastMsg(`Compte créé ! Bienvenue, ${data.user?.name || fullName} !`);
      setShowToast(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-brand-50 py-8">
      <Toast
        message={toastMessage}
        visible={showToast}
        onClose={() => {
          if (pendingAuth.current) { login(pendingAuth.current); pendingAuth.current = null; }
          navigate("/dashboard", { replace: true });
        }}
        duration={3000}
      />
      <BlobBackground opacity={0.15} className="pointer-events-none absolute inset-0 z-0" />

      <div className="relative z-10 mx-4 w-full max-w-md">
        <div className="rounded-2xl border border-brand-border bg-white p-8 shadow-card-md space-y-5">

          {/* Header */}
          <div className="flex flex-col items-center gap-2 text-center">
            <img src="/logo%20brand%20ai.png" alt="BrandAI" className="h-12 w-auto" />
            <h1 className="text-2xl font-extrabold text-ink">Créer un compte</h1>
            <p className="text-sm text-ink-muted">Rejoignez BrandAI gratuitement</p>
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
          <div className="flex items-center gap-3">
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

            {/* Prénom + Nom */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: "reg-prenom", label: "Prénom", value: prenom, setValue: setPrenom, field: "prenom", placeholder: "Ahmed", err: prenomError },
                { id: "reg-nom",    label: "Nom",    value: nom,    setValue: setNom,    field: "nom",    placeholder: "Ben Ali", err: nomError },
              ].map(({ id, label, value, setValue, field, placeholder, err }) => (
                <div key={id}>
                  <label htmlFor={id} className="mb-1.5 block text-sm font-semibold text-ink">{label}</label>
                  <div className="relative">
                    <HiOutlineUser className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-subtle" />
                    <input
                      id={id} type="text" value={value} placeholder={placeholder}
                      onChange={(e) => setValue(e.target.value)}
                      onBlur={() => handleBlur(field)}
                      className={getInputClass(!!err, !!value.trim(), touched[field])}
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2">
                      <FieldIcon error={err} touched={touched[field]} value={value.trim()} />
                    </span>
                  </div>
                  {err && <p className="mt-1.5 text-xs text-red-500">{err}</p>}
                </div>
              ))}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="reg-email" className="mb-1.5 block text-sm font-semibold text-ink">Email</label>
              <div className="relative">
                <HiOutlineEnvelope className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-subtle" />
                <input
                  id="reg-email" type="email" value={email} placeholder="vous@exemple.com"
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={() => handleBlur("email")}
                  className={getInputClass(!!emailError, !!email.trim(), touched.email)}
                />
                <span className="absolute right-3.5 top-1/2 -translate-y-1/2">
                  <FieldIcon error={emailError} touched={touched.email} value={email.trim()} />
                </span>
              </div>
              {emailError && <p className="mt-1.5 text-xs text-red-500">{emailError}</p>}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="reg-password" className="mb-1.5 block text-sm font-semibold text-ink">Mot de passe</label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-subtle" />
                <input
                  id="reg-password" type={showPassword ? "text" : "password"} value={password} placeholder="••••••••"
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => handleBlur("password")}
                  className={getInputClass(!!passwordError, !!password, touched.password, true)}
                />
                <span className="absolute right-3.5 top-1/2 flex -translate-y-1/2 items-center gap-1">
                  <button type="button" onClick={() => setShowPwd((v) => !v)} className="text-ink-subtle hover:text-ink">
                    {showPassword ? <HiOutlineEyeSlash className="h-5 w-5" /> : <HiOutlineEye className="h-5 w-5" />}
                  </button>
                  <FieldIcon error={passwordError} touched={touched.password} value={password} />
                </span>
              </div>
              {/* Strength bar */}
              {password && (
                <div className="mt-2">
                  <div className="flex gap-1">
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-all ${
                          passwordStrength.level >= i ? passwordStrength.color : "bg-gray-200"
                        }`}
                      />
                    ))}
                  </div>
                  <p className={`mt-1 text-xs ${
                    passwordStrength.level === 1 ? "text-red-500" :
                    passwordStrength.level === 2 ? "text-amber-500" : "text-success"
                  }`}>
                    {passwordStrength.label}
                  </p>
                </div>
              )}
              {passwordError && <p className="mt-1.5 text-xs text-red-500">{passwordError}</p>}
            </div>

            {/* Confirm */}
            <div>
              <label htmlFor="reg-confirm" className="mb-1.5 block text-sm font-semibold text-ink">Confirmer le mot de passe</label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-subtle" />
                <input
                  id="reg-confirm" type={showConfirm ? "text" : "password"} value={confirm} placeholder="••••••••"
                  onChange={(e) => setConfirm(e.target.value)}
                  onBlur={() => handleBlur("confirm")}
                  className={getInputClass(!!confirmError, !!confirm, touched.confirm, true)}
                />
                <span className="absolute right-3.5 top-1/2 flex -translate-y-1/2 items-center gap-1">
                  <button type="button" onClick={() => setShowConfirm((v) => !v)} className="text-ink-subtle hover:text-ink">
                    {showConfirm ? <HiOutlineEyeSlash className="h-5 w-5" /> : <HiOutlineEye className="h-5 w-5" />}
                  </button>
                  <FieldIcon error={confirmError} touched={touched.confirm} value={confirm} />
                </span>
              </div>
              {confirmError && <p className="mt-1.5 text-xs text-red-500">{confirmError}</p>}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={!isFormValid || loading}
              className="flex h-11 w-full items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-sm font-bold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading
                ? <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                : "Créer mon compte"}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-sm text-ink-muted">
            Déjà un compte ?{" "}
            <Link to="/login" className="font-semibold text-brand hover:underline">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
