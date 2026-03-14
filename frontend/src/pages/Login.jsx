import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { HiOutlineEnvelope, HiOutlineLockClosed } from "react-icons/hi2";
import { FcGoogle } from "react-icons/fc";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { BlobBackground } from "../components/ui/BlobBackground";
import { MOCK_USER_GOOGLE, MOCK_USER_EMAIL } from "../data/mockData";
import { useAuth } from "../hooks/useAuth";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleGoogleLogin = () => { login(MOCK_USER_GOOGLE); navigate("/dashboard", { replace: true }); };
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;
    login({ ...MOCK_USER_EMAIL, name: email.split("@")[0] || "Utilisateur", email: email.trim() });
    navigate("/dashboard", { replace: true });
  };

  return (
    <div className="relative min-h-screen bg-white">
      <BlobBackground opacity={0.35} className="pointer-events-none z-0" />
      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-12">
        <Card className="w-full max-w-[420px] shadow-[0_8px_32px_rgba(0,0,0,0.06),0_2px_8px_rgba(124,58,237,0.04)]" hover={false}>
          <div className="flex flex-col items-center text-center">
            <img src="/logo%20brand%20ai.png" alt="BrandAI" className="mb-4 h-14 w-auto object-contain" />
            <h1 className="mb-2 text-xl font-semibold text-[#111827]">Bienvenue sur BrandAI</h1>
            <p className="mb-6 text-[#6B7280]">Connectez-vous pour continuer</p>
          </div>
          <button type="button" onClick={handleGoogleLogin} className="mb-6 flex w-full items-center justify-center gap-3 rounded-[10px] border border-[#E5E7EB] bg-white py-3 font-medium text-[#111827] transition-all duration-200 hover:border-violet-300 hover:bg-[#F9FAFB]">
            <FcGoogle className="h-5 w-5" /> Continuer avec Google
          </button>
          <div className="relative mb-6"><div className="absolute inset-0 flex items-center"><div className="w-full border-t border-[#E5E7EB]" /></div><div className="relative flex justify-center"><span className="bg-white px-3 text-sm text-[#6B7280]">ou</span></div></div>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div><label htmlFor="login-email" className="mb-1.5 block text-sm font-medium text-[#111827]">Email</label><div className="relative"><HiOutlineEnvelope className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" /><input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vous@exemple.com" className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]" /></div></div>
            <div><label htmlFor="login-password" className="mb-1.5 block text-sm font-medium text-[#111827]">Mot de passe</label><div className="relative"><HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" /><input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]" /></div></div>
            <Button type="submit" variant="primary" fullWidth disabled={!email || !password}>Se connecter</Button>
          </form>
          <p className="mt-6 text-center text-sm text-[#6B7280]">Pas encore de compte ? <Link to="/register" className="font-medium text-[#7C3AED] hover:underline">S'inscrire</Link></p>
        </Card>
      </div>
    </div>
  );
}

export default Login;
