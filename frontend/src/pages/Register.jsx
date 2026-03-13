import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { HiOutlineBolt, HiOutlineUser, HiOutlineEnvelope, HiOutlineLockClosed } from "react-icons/hi2";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { BlobBackground } from "../components/ui/BlobBackground";
import { useAuth } from "../hooks/useAuth";

export function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password || password !== confirm) return;
    login({ name: name.trim(), email: email.trim(), avatar: null, loginMethod: "email" });
    navigate("/dashboard", { replace: true });
  };
  const isValid = name.trim() && email.trim() && password.length >= 6 && password === confirm;

  return (
    <div className="relative min-h-screen bg-white">
      <BlobBackground opacity={0.35} className="pointer-events-none z-0" />
      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-12">
        <Card className="w-full max-w-[420px]" hover={false}>
          <div className="flex flex-col items-center text-center">
            <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#7C3AED]/10 text-[#7C3AED]"><HiOutlineBolt className="h-7 w-7" /></span>
            <h1 className="mb-2 text-xl font-semibold text-[#111827]">Créer un compte</h1>
            <p className="mb-6 text-[#6B7280]">Rejoignez BrandAI</p>
          </div>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div><label htmlFor="reg-name" className="mb-1.5 block text-sm font-medium text-[#111827]">Nom</label><div className="relative"><HiOutlineUser className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" /><input id="reg-name" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Ahmed Ben Ali" className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]" /></div></div>
            <div><label htmlFor="reg-email" className="mb-1.5 block text-sm font-medium text-[#111827]">Email</label><div className="relative"><HiOutlineEnvelope className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" /><input id="reg-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vous@exemple.com" className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]" /></div></div>
            <div><label htmlFor="reg-password" className="mb-1.5 block text-sm font-medium text-[#111827]">Mot de passe</label><div className="relative"><HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" /><input id="reg-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]" /></div></div>
            <div><label htmlFor="reg-confirm" className="mb-1.5 block text-sm font-medium text-[#111827]">Confirmer le mot de passe</label><div className="relative"><HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B7280]" /><input id="reg-confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="••••••••" className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2.5 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]" /></div></div>
            <Button type="submit" variant="primary" fullWidth disabled={!isValid}>S'inscrire</Button>
          </form>
          <p className="mt-6 text-center text-sm text-[#6B7280]">Déjà un compte ? <Link to="/login" className="font-medium text-[#7C3AED] hover:underline">Se connecter</Link></p>
        </Card>
      </div>
    </div>
  );
}

export default Register;
