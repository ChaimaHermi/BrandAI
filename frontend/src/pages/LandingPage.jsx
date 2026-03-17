import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  HiOutlineSparkles,
  HiOutlineRocketLaunch,
  HiOutlinePlayCircle,
  HiOutlineMagnifyingGlass,
  HiOutlinePaintBrush,
  HiOutlineGlobeAlt,
  HiOutlineLightBulb,
  HiOutlineDocumentText,
  HiOutlineChartBarSquare,
  HiOutlineCheckCircle,
  HiOutlineClock,
  HiOutlineUserGroup,
} from "react-icons/hi2";
import { FiTarget } from "react-icons/fi";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { BlobBackground } from "@/components/ui/BlobBackground";

const AGENTS_PREVIEW = [
  { id: "idea", name: "Idea Enhancer", Icon: HiOutlineLightBulb, status: "done" },
  { id: "market", name: "Market Analysis", Icon: HiOutlineMagnifyingGlass, status: "done" },
  { id: "brand", name: "Brand Identity", Icon: HiOutlinePaintBrush, status: "running" },
  { id: "content", name: "Content Creator", Icon: HiOutlineDocumentText, status: "waiting" },
  { id: "website", name: "Website Builder", Icon: HiOutlineGlobeAlt, status: "waiting" },
  { id: "optimizer", name: "Optimizer", Icon: HiOutlineChartBarSquare, status: "waiting" },
];

const AGENTS_CARDS = [
  { Icon: HiOutlineLightBulb, name: "Idea Enhancer", description: "Enrichit et structure votre idée initiale. Définit la proposition de valeur, la cible et le positionnement stratégique." },
  { Icon: HiOutlineMagnifyingGlass, name: "Market Analysis", description: "Analyse la concurrence, identifie les tendances du marché et évalue les opportunités et risques de votre secteur." },
  { Icon: HiOutlinePaintBrush, name: "Brand Identity", description: "Génère le nom de marque, le slogan, la palette de couleurs, le style visuel et les guidelines de votre identité." },
  { Icon: HiOutlineDocumentText, name: "Content Creator", description: "Crée des publications optimisées pour Instagram, LinkedIn, Twitter et autres réseaux sociaux adaptées à votre marque." },
  { Icon: HiOutlineGlobeAlt, name: "Website Builder", description: "Génère automatiquement un site web vitrine responsive et moderne aligné sur votre identité de marque." },
  { Icon: HiOutlineChartBarSquare, name: "Optimizer", description: "Analyse les performances de vos contenus et propose des recommandations concrètes pour améliorer votre stratégie digitale." },
];

const STEPS = [
  { number: "01", title: "Décrivez votre projet", description: "Saisissez votre idée de startup, choisissez votre secteur et décrivez votre vision en quelques lignes." },
  { number: "02", title: "Les agents IA s'activent", description: "Notre pipeline de 6 agents spécialisés analyse, crée et optimise votre marque en temps réel sous vos yeux." },
  { number: "03", title: "Récupérez votre marque", description: "Téléchargez votre analyse, identité, contenus et site web. Prêt à lancer votre startup sur le marché." },
];

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className="relative min-h-screen bg-white">
      <div className="flex min-h-screen flex-col">
        <Navbar variant="landing" />
        <main className="flex-1">
          <section className="relative overflow-hidden bg-white py-16 md:py-20">
            <BlobBackground opacity={0.4} />
            <div className="relative z-10 mx-auto max-w-[1200px] px-4 md:px-6">
              <div className="grid gap-12 lg:grid-cols-2 lg:items-center lg:gap-16">
                <div className={`transition-all duration-700 ${mounted ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"}`}>
                  <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#E5E7EB] bg-[#F9FAFB] px-4 py-1.5 text-sm text-[#6B7280]">
                    <HiOutlineSparkles className="h-4 w-4 text-[#7C3AED]" /> IA Générative & Agentique
                  </span>
                  <h1 className="mb-4 text-4xl font-semibold leading-tight tracking-tight text-[#111827] md:text-5xl">
                    From the idea
                    <br />
                    to go to the market
                  </h1>
                  <p className="mb-8 max-w-[520px] text-lg text-[#6B7280]">
                    Décrivez votre projet. Nos agents IA génèrent l'analyse de marché, l'identité de marque et les contenus en quelques clics.
                  </p>
                  <div className="flex flex-wrap gap-4">
                    <Link to="/register" className="inline-flex items-center justify-center gap-2 rounded-[10px] bg-[#7C3AED] px-5 py-2.5 font-medium text-white transition-all duration-200 hover:scale-[1.02] hover:bg-[#6D28D9] active:scale-[0.98]">
                      <HiOutlineRocketLaunch className="h-5 w-5" /> Lancer mon projet
                    </Link>
                    <Link to="/login" className="inline-flex items-center justify-center gap-2 rounded-[10px] border border-[#E5E7EB] bg-white px-5 py-2.5 font-medium text-[#111827] transition-all duration-200 hover:border-violet-300 hover:text-[#7C3AED]">
                      <HiOutlinePlayCircle className="h-5 w-5" /> Voir la démo
                    </Link>
                  </div>
                </div>
                <div className={`hidden transition-all duration-700 delay-200 lg:block ${mounted ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"}`}>
                  <Card className="border border-[#E5E7EB] bg-white shadow-[0_8px_32px_rgba(0,0,0,0.06),0_2px_8px_rgba(124,58,237,0.04)]" hover={false}>
                    <div className="rounded-lg border border-[#E5E7EB] bg-white p-4">
                      <p className="mb-3 text-sm font-medium text-[#6B7280]">Pipeline IA — aperçu</p>
                      <div className="space-y-2">
                        {AGENTS_PREVIEW.map(({ id, name, Icon, status }) => (
                          <div
                            key={id}
                            className={`flex items-center gap-3 rounded-lg border p-2.5 transition-all ${status === "running" ? "border-[#7C3AED] bg-[#F5F3FF]/50" : "border-[#E5E7EB]"} ${status === "waiting" ? "opacity-60" : ""}`}
                          >
                            <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${status === "done" ? "bg-[#DCFCE7] text-[#16A34A]" : status === "running" ? "bg-[#7C3AED]/10 text-[#7C3AED]" : "bg-[#F9FAFB] text-[#9CA3AF]"}`}>
                              {status === "done" ? <HiOutlineCheckCircle className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                            </span>
                            <div className="min-w-0 flex-1">
                              <p className="text-sm font-medium text-[#111827]">{name}</p>
                              <div className="mt-0.5 flex items-center gap-2">
                                {status === "done" && <span className="text-xs text-[#16A34A]">Terminé</span>}
                                {status === "running" && (
                                  <>
                                    <span className="text-xs font-medium text-[#7C3AED]">En cours</span>
                                    <div className="h-1 max-w-[80px] flex-1 overflow-hidden rounded-full bg-[#E5E7EB]">
                                      <div className="h-full w-[45%] animate-progress-bar rounded-full bg-[#7C3AED]" />
                                    </div>
                                  </>
                                )}
                                {status === "waiting" && (
                                  <span className="flex items-center gap-1 text-xs text-[#9CA3AF]">
                                    <HiOutlineClock className="h-3 w-3" /> En attente
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            </div>
          </section>

          <section className="bg-[#F9FAFB] py-16 md:py-20">
            <div className="mx-auto max-w-[1200px] px-4 md:px-6">
              <h2 className="mb-3 text-center text-2xl font-semibold text-[#111827] md:text-3xl">Nos agents IA travaillent pour vous</h2>
              <p className="mx-auto mb-12 max-w-[560px] text-center text-[#6B7280]">
                Un pipeline intelligent qui transforme votre idée en marque complète, étape par étape.
              </p>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {AGENTS_CARDS.map(({ Icon, name, description }) => (
                  <Card key={name} className="border border-[#E5E7EB] bg-white shadow-[0_8px_32px_rgba(0,0,0,0.06),0_2px_8px_rgba(124,58,237,0.04)] hover:border-[#A78BFA] hover:-translate-y-[2px]">
                    <div className="mb-3 flex items-start justify-between gap-2">
                      <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#7C3AED]/10 text-[#7C3AED]">
                        <Icon className="h-5 w-5" />
                      </span>
                      <Badge variant="violet">Agent IA</Badge>
                    </div>
                    <h3 className="mb-2 font-semibold text-[#111827]">{name}</h3>
                    <p className="text-[#6B7280]">{description}</p>
                  </Card>
                ))}
              </div>

              <div className="mt-8 flex flex-col items-center gap-6 rounded-[12px] border border-[#DDD6FE] bg-[#F5F3FF] p-6 shadow-[0_8px_32px_rgba(0,0,0,0.06),0_2px_8px_rgba(124,58,237,0.04)] md:flex-row md:items-center md:justify-between md:px-8 md:py-6">
                <div className="flex items-center gap-6">
                  <span className="flex h-[36px] w-[36px] shrink-0 items-center justify-center text-[28px]">
                    <HiOutlineChartBarSquare className="h-9 w-9 text-[#7C3AED]" />
                  </span>
                  <div>
                    <h3 className="mb-1 text-base font-medium text-[#111827]">Stratégie marketing complète</h3>
                    <p className="text-[13px] text-[#6B7280]">Positionnement, personas, canaux prioritaires et plan de lancement go-to-market structuré.</p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-[20px] border border-[#DDD6FE] bg-white px-3.5 py-1.5 text-xs text-[#111827]">
                    <HiOutlineUserGroup className="h-3.5 w-3.5 text-[#7C3AED]" /> Personas & cibles
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-[20px] border border-[#DDD6FE] bg-white px-3.5 py-1.5 text-xs text-[#111827]">
                    <FiTarget className="h-3.5 w-3.5 text-[#7C3AED]" /> Positionnement marché
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-[20px] border border-[#DDD6FE] bg-white px-3.5 py-1.5 text-xs text-[#111827]">
                    <HiOutlineRocketLaunch className="h-3.5 w-3.5 text-[#7C3AED]" /> Plan de lancement
                  </span>
                </div>
              </div>
            </div>
          </section>

          <section className="bg-white py-16 md:py-20">
            <div className="mx-auto max-w-[1200px] px-4 md:px-6">
              <h2 className="mb-3 text-center text-2xl font-semibold text-[#111827] md:text-3xl">Comment ça marche ?</h2>
              <p className="mx-auto mb-12 max-w-[560px] text-center text-[#6B7280]">
                3 étapes simples pour transformer votre idée en marque complète.
              </p>
              <div className="relative">
                <div className="hidden items-start justify-between md:flex">
                  <div className="absolute left-[16.666%] right-[16.666%] top-6 border-t-2 border-dashed border-[#DDD6FE]" aria-hidden />
                  {STEPS.map((step) => (
                    <div key={step.number} className="relative z-10 flex flex-1 flex-col items-center px-4 text-center">
                      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#7C3AED] text-sm font-semibold text-white">{step.number}</div>
                      <h3 className="mb-2 font-semibold text-[#111827]">{step.title}</h3>
                      <p className="max-w-[260px] text-sm text-[#6B7280]">{step.description}</p>
                    </div>
                  ))}
                </div>
                <div className="flex flex-col gap-8 md:hidden">
                  {STEPS.map((step) => (
                    <div key={step.number} className="flex gap-4 text-left">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#7C3AED] text-sm font-semibold text-white">{step.number}</div>
                      <div>
                        <h3 className="mb-1 font-semibold text-[#111827]">{step.title}</h3>
                        <p className="text-sm text-[#6B7280]">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </main>
        <Footer />
      </div>
    </div>
  );
}

