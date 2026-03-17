import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { HiOutlineRocketLaunch, HiOutlineMagnifyingGlass, HiOutlinePaintBrush, HiOutlineDevicePhoneMobile, HiOutlineGlobeAlt, HiOutlineChartBar, HiOutlineSparkles } from "react-icons/hi2";
import { Navbar } from "../components/layout/Navbar";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { SECTORS } from "@/shared/utils/mockData";

const GENERATED_ITEMS = [
  { icon: HiOutlineMagnifyingGlass, label: "Analyse marché" },
  { icon: HiOutlinePaintBrush, label: "Identité de marque" },
  { icon: HiOutlineDevicePhoneMobile, label: "Posts réseaux sociaux" },
  { icon: HiOutlineGlobeAlt, label: "Site web vitrine" },
  { icon: HiOutlineChartBar, label: "Stratégie marketing" },
  { icon: HiOutlineSparkles, label: "Recommandations" },
];

const inputFocusClass =
  "w-full rounded-[10px] border border-[#E5E7EB] bg-white px-4 py-2.5 text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-0 focus:shadow-[0_0_0_3px_rgba(124,58,237,0.1)]";

export function NewProject() {
  const [name, setName] = useState("");
  const [sector, setSector] = useState("");
  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const canSubmit = name.trim() && sector && idea.trim();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSubmit || loading) return;
    setLoading(true);
    setTimeout(() => navigate("/projects/techmentor", { replace: true }), 1500);
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      <Navbar variant="app" />
      <main className="flex flex-1 items-center justify-center overflow-hidden px-6">
        <div className="w-full max-w-[700px]">
          <h1 className="mb-4 text-xl font-semibold text-[#111827]">
            Nouveau projet
          </h1>
          <Card
            hover={false}
            className="border border-[#E5E7EB] bg-white rounded-xl shadow-sm p-6"
          >
            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <div>
                <label htmlFor="project-name" className="mb-1.5 block text-sm font-medium text-[#111827]">Nom du projet</label>
                <input id="project-name" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Mon super projet" className={inputFocusClass} />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="project-sector" className="mb-1.5 block text-sm font-medium text-[#111827]">Secteur</label>
                <select id="project-sector" value={sector} onChange={(e) => setSector(e.target.value)} className={inputFocusClass}>
                  <option value="">Sélectionner un secteur</option>
                  {SECTORS.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label htmlFor="project-idea" className="mb-1.5 block text-sm font-medium text-[#111827]">Idée du projet</label>
                <textarea
                  id="project-idea"
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  placeholder="Décrivez votre idée en quelques phrases..."
                  className={`resize-none h-[120px] ${inputFocusClass}`}
                />
              </div>
              <div className="rounded-[10px] border border-[#DDD6FE] bg-[#F5F3FF] p-4 space-y-3">
                <p className="mb-3 text-sm font-medium text-[#7C3AED]">Ce qui sera généré</p>
                <ul className="grid gap-2 sm:grid-cols-2">
                  {GENERATED_ITEMS.map(({ icon: Icon, label }) => (
                    <li key={label} className="flex items-center gap-2 text-sm text-[#6B7280]">
                      <Icon className="h-4 w-4 shrink-0 text-[#7C3AED]" />
                      {label}
                    </li>
                  ))}
                </ul>
              </div>
              <Button
                type="submit"
                variant="primary"
                fullWidth
                disabled={!canSubmit || loading}
                className="gap-2 py-2.5"
              >
                {loading ? <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" /> : <HiOutlineRocketLaunch className="h-5 w-5" />}
                {loading ? "Lancement en cours..." : "Lancer le pipeline IA"}
              </Button>
            </form>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default NewProject;
