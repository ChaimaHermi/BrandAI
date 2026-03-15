// ==============================================================
//  frontend/src/pages/Register.jsx
//  RÔLE : Page d'inscription connectée au vrai backend
//
//  VALIDATION CÔTÉ CLIENT (on blur) :
//    - name : min 2 caractères, pas de chiffres
//    - email : format email valide (regex)
//    - password : min 6 caractères, 1 majuscule, 1 chiffre
//    - confirm : doit correspondre exactement au password
//
//  FEEDBACK VISUEL :
//    - Champ valide → bordure verte + icône check
//    - Champ invalide → bordure rouge + icône X
//    - Indicateur de force du mot de passe (Faible/Moyen/Fort)
//    - Toggle show/hide password
//    - Spinner dans le bouton pendant l'API call
// ==============================================================

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
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { BlobBackground } from "../components/ui/BlobBackground";
import { Toast } from "../components/ui/Toast";
import { useAuth } from "../hooks/useAuth";
import { apiRegister } from "../services/authApi";

// ── Validateurs (exécutés on blur) ─────────────────────────────
const validateNameField = (value, fieldLabel) => {
  if (!value.trim()) return "";
  if (value.trim().length < 2) return `Le ${fieldLabel} doit contenir au moins 2 caractères.`;
  if (/\d/.test(value)) return `Le ${fieldLabel} ne doit pas contenir de chiffres.`;
  return "";
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const validateEmail = (value) => {
  if (!value.trim()) return "";
  if (!EMAIL_REGEX.test(value.trim())) return "Veuillez entrer une adresse email valide.";
  return "";
};

const validatePassword = (value) => {
  if (!value) return "";
  if (value.length < 6) return "Le mot de passe doit contenir au moins 6 caractères.";
  if (!/[A-Z]/.test(value)) return "Le mot de passe doit contenir au moins une majuscule.";
  if (!/\d/.test(value)) return "Le mot de passe doit contenir au moins un chiffre.";
  return "";
};

const validateConfirm = (confirm, password) => {
  if (!confirm) return "";
  if (confirm !== password) return "Les mots de passe ne correspondent pas.";
  return "";
};

// ── Indicateur de force du mot de passe ─────────────────────────
// 1 condition (length ≥ 6) → Faible (rouge)
// 2 conditions (+ majuscule) → Moyen (orange)
// 3 conditions (+ chiffre) → Fort (vert)
function getPasswordStrength(password) {
  if (!password) return { level: 0, label: "", color: "" };
  let met = 0;
  if (password.length >= 6) met++;
  if (/[A-Z]/.test(password)) met++;
  if (/\d/.test(password)) met++;
  if (met === 1) return { level: 1, label: "Faible", color: "bg-red-500" };
  if (met === 2) return { level: 2, label: "Moyen", color: "bg-orange-500" };
  return { level: 3, label: "Fort", color: "bg-green-500" };
}

export function Register() {
  const [prenom, setPrenom] = useState("");
  const [nom, setNom] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  // Touched = champs déjà visités (pour afficher les erreurs on blur)
  const [touched, setTouched] = useState({ prenom: false, nom: false, email: false, password: false, confirm: false });

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

  const prenomError = touched.prenom ? validateNameField(prenom, "prénom") : "";
  const nomError = touched.nom ? validateNameField(nom, "nom") : "";
  const emailError = touched.email ? validateEmail(email) : "";
  const passwordError = touched.password ? validatePassword(password) : "";
  const confirmError = touched.confirm ? validateConfirm(confirm, password) : "";

  const fullName = `${prenom.trim()} ${nom.trim()}`.trim();

  const isFormValid =
    !prenomError &&
    !nomError &&
    !emailError &&
    !passwordError &&
    !confirmError &&
    prenom.trim().length >= 2 &&
    !/\d/.test(prenom.trim()) &&
    nom.trim().length >= 2 &&
    !/\d/.test(nom.trim()) &&
    EMAIL_REGEX.test(email.trim()) &&
    password.length >= 6 &&
    /[A-Z]/.test(password) &&
    /\d/.test(password) &&
    confirm === password;

  const passwordStrength = getPasswordStrength(password);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isFormValid) return;

    setError("");
    setLoading(true);

    try {
      const data = await apiRegister({ name: fullName, email, password });
      pendingAuthData.current = data;

      setToastMessage(`Compte créé avec succès ! Bienvenue sur BrandAI, ${data.user?.name || fullName} !`);
      setShowToast(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const inputBase =
    "w-full rounded-[10px] bg-white py-2.5 pl-10 text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-1 ";
  const inputValid = "border border-green-400 focus:border-green-500 focus:ring-green-500";
  const inputInvalid = "border border-red-400 focus:border-red-500 focus:ring-red-500";
  const inputNeutral = "border border-[#E5E7EB] focus:border-[#7C3AED] focus:ring-[#7C3AED]";

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

  return (
    <div className="relative min-h-screen bg-white">
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
        duration={3000}
      />
      <BlobBackground opacity={0.35} className="pointer-events-none z-0" />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-12">
        <Card
          className="w-full max-w-[420px] shadow-[0_8px_32px_rgba(0,0,0,0.06)]"
          hover={false}
        >
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

          {(searchParams.get("error") === "google_failed" || searchParams.get("error") === "google_auth_failed") && (
            <div className="mb-4 rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              Connexion Google échouée. Veuillez réessayer.
            </div>
          )}

          <button
            type="button"
            onClick={handleGoogleLogin}
            className="mb-6 flex w-full items-center justify-center gap-3 rounded-[10px] border border-[#E5E7EB] bg-white py-3 font-medium text-[#111827] transition-all hover:border-violet-300 hover:bg-[#F9FAFB]"
          >
            <FcGoogle className="h-5 w-5" /> Continuer avec Google
          </button>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#E5E7EB]" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-sm text-[#6B7280]">ou</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <div className="rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Prénom et Nom sur une seule ligne */}
            <div className="flex gap-3">
              <div className="flex-1">
                <label htmlFor="reg-prenom" className="mb-1.5 block text-sm font-medium text-[#111827]">
                  Prénom
                </label>
                <div className="relative">
                  <HiOutlineUser className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                  <input
                    id="reg-prenom"
                    type="text"
                    value={prenom}
                    onChange={(e) => setPrenom(e.target.value)}
                    onBlur={() => handleBlur("prenom")}
                    placeholder="Ahmed"
                    className={getInputClass(!!prenomError, !!prenom.trim(), touched.prenom, false)}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2">
                    <FieldIcon error={prenomError} touched={touched.prenom} value={prenom.trim()} />
                  </span>
                </div>
                {prenomError && <p className="mt-1 text-xs text-red-500">{prenomError}</p>}
              </div>
              <div className="flex-1">
                <label htmlFor="reg-nom" className="mb-1.5 block text-sm font-medium text-[#111827]">
                  Nom
                </label>
                <div className="relative">
                  <HiOutlineUser className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                  <input
                    id="reg-nom"
                    type="text"
                    value={nom}
                    onChange={(e) => setNom(e.target.value)}
                    onBlur={() => handleBlur("nom")}
                    placeholder="Ben Ali"
                    className={getInputClass(!!nomError, !!nom.trim(), touched.nom, false)}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2">
                    <FieldIcon error={nomError} touched={touched.nom} value={nom.trim()} />
                  </span>
                </div>
                {nomError && <p className="mt-1 text-xs text-red-500">{nomError}</p>}
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="reg-email" className="mb-1.5 block text-sm font-medium text-[#111827]">
                Email
              </label>
              <div className="relative">
                <HiOutlineEnvelope className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="reg-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={() => handleBlur("email")}
                  placeholder="vous@exemple.com"
                  className={getInputClass(!!emailError, !!email.trim(), touched.email, false)}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2">
                  <FieldIcon error={emailError} touched={touched.email} value={email.trim()} />
                </span>
              </div>
              {emailError && <p className="mt-1 text-xs text-red-500">{emailError}</p>}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="reg-password" className="mb-1.5 block text-sm font-medium text-[#111827]">
                Mot de passe
              </label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="reg-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => handleBlur("password")}
                  placeholder="••••••••"
                  className={getInputClass(!!passwordError, !!password, touched.password, true)}
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
                  <FieldIcon error={passwordError} touched={touched.password} value={password} />
                </span>
              </div>
              {/* Indicateur de force */}
              {password && (
                <div className="mt-1.5">
                  <div className="flex gap-1">
                    <div
                      className={`h-1 flex-1 rounded ${passwordStrength.level >= 1 ? passwordStrength.color : "bg-gray-200"}`}
                    />
                    <div
                      className={`h-1 flex-1 rounded ${passwordStrength.level >= 2 ? passwordStrength.color : "bg-gray-200"}`}
                    />
                    <div
                      className={`h-1 flex-1 rounded ${passwordStrength.level >= 3 ? passwordStrength.color : "bg-gray-200"}`}
                    />
                  </div>
                  <p className={`mt-0.5 text-xs ${passwordStrength.level === 1 ? "text-red-500" : passwordStrength.level === 2 ? "text-orange-500" : "text-green-600"}`}>
                    {passwordStrength.label}
                  </p>
                </div>
              )}
              {passwordError && <p className="mt-1 text-xs text-red-500">{passwordError}</p>}
            </div>

            {/* Confirm password */}
            <div>
              <label htmlFor="reg-confirm" className="mb-1.5 block text-sm font-medium text-[#111827]">
                Confirmer le mot de passe
              </label>
              <div className="relative">
                <HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" />
                <input
                  id="reg-confirm"
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  onBlur={() => handleBlur("confirm")}
                  placeholder="••••••••"
                  className={getInputClass(!!confirmError, !!confirm, touched.confirm, true)}
                />
                <span className="absolute right-10 top-1/2 flex -translate-y-1/2 items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="text-[#6B7280] hover:text-[#111827]"
                    aria-label={showConfirmPassword ? "Masquer" : "Afficher"}
                  >
                    {showConfirmPassword ? <HiOutlineEyeSlash className="h-5 w-5" /> : <HiOutlineEye className="h-5 w-5" />}
                  </button>
                  <FieldIcon error={confirmError} touched={touched.confirm} value={confirm} />
                </span>
              </div>
              {confirmError && <p className="mt-1 text-xs text-red-500">{confirmError}</p>}
            </div>

            <Button
              type="submit"
              variant="primary"
              fullWidth
              disabled={!isFormValid || loading}
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
            <Link to="/login" className="font-medium text-[#7C3AED] hover:underline">
              Se connecter
            </Link>
          </p>
        </Card>
      </div>
    </div>
  );
}

export default Register;
