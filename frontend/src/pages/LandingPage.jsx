import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  HiOutlineSparkles,
  HiOutlineRocketLaunch,
  HiOutlineMagnifyingGlass,
  HiOutlinePaintBrush,
  HiOutlineGlobeAlt,
  HiOutlineLightBulb,
  HiOutlineDocumentText,
  HiOutlineChartBarSquare,
  HiOutlineCheckCircle,
  HiOutlineClock,
  HiOutlineUserGroup,
  HiOutlineArrowRight,
} from "react-icons/hi2";
import { FiTarget } from "react-icons/fi";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { BlobBackground } from "@/components/ui/BlobBackground";

/* ─────────────────────────────────────────────────────────────────────────────
   Static data
───────────────────────────────────────────────────────────────────────────── */
const AGENTS_PREVIEW = [
  { id: "idea",      name: "Idea Enhancer",   Icon: HiOutlineLightBulb,       status: "done"    },
  { id: "market",    name: "Market Analysis", Icon: HiOutlineMagnifyingGlass,  status: "done"    },
  { id: "brand",     name: "Brand Identity",  Icon: HiOutlinePaintBrush,       status: "running" },
  { id: "content",   name: "Content Creator", Icon: HiOutlineDocumentText,     status: "waiting" },
  { id: "website",   name: "Website Builder", Icon: HiOutlineGlobeAlt,         status: "waiting" },
  { id: "optimizer", name: "Optimizer",       Icon: HiOutlineChartBarSquare,   status: "waiting" },
];

const AGENTS_CARDS = [
  { Icon: HiOutlineLightBulb,     name: "Idea Enhancer",   description: "Enrichit et structure votre idée initiale. Définit la proposition de valeur, la cible et le positionnement stratégique." },
  { Icon: HiOutlineMagnifyingGlass, name: "Market Analysis", description: "Analyse la concurrence, identifie les tendances du marché et évalue les opportunités et risques de votre secteur." },
  { Icon: HiOutlinePaintBrush,    name: "Brand Identity",  description: "Génère le nom de marque, le slogan, la palette de couleurs, le style visuel et les guidelines de votre identité." },
  { Icon: HiOutlineDocumentText,  name: "Content Creator", description: "Crée des publications optimisées pour Instagram, LinkedIn, Twitter et autres réseaux sociaux adaptées à votre marque." },
  { Icon: HiOutlineGlobeAlt,      name: "Website Builder", description: "Génère automatiquement un site web vitrine responsive et moderne aligné sur votre identité de marque." },
  { Icon: HiOutlineChartBarSquare,name: "Optimizer",       description: "Analyse les performances de vos contenus et propose des recommandations concrètes pour améliorer votre stratégie digitale." },
];

const STEPS = [
  { number: "01", title: "Décrivez votre projet",    description: "Saisissez votre idée de startup, choisissez votre secteur et décrivez votre vision en quelques lignes." },
  { number: "02", title: "Les agents IA s'activent", description: "Notre pipeline de 6 agents spécialisés analyse, crée et optimise votre marque en temps réel sous vos yeux." },
  { number: "03", title: "Récupérez votre marque",   description: "Téléchargez votre analyse, identité, contenus et site web. Prêt à lancer votre startup sur le marché." },
];

const MARKETING_TAGS = [
  { Icon: HiOutlineUserGroup, label: "Personas & cibles"      },
  { Icon: FiTarget,           label: "Positionnement marché"  },
  { Icon: HiOutlineRocketLaunch, label: "Plan de lancement"   },
];

/* ─────────────────────────────────────────────────────────────────────────────
   Sub-components
───────────────────────────────────────────────────────────────────────────── */

/** Agent status row in the hero preview card */
function AgentPreviewRow({ name, Icon, status }) {
  return (
    <div
      className={`flex items-center gap-3 rounded-xl border p-3 transition-all ${
        status === "running"
          ? "border-brand bg-brand-light/60"
          : status === "done"
            ? "border-brand-border bg-white"
            : "border-gray-100 bg-gray-50 opacity-60"
      }`}
    >
      {/* Icon bubble */}
      <span
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
          status === "done"    ? "bg-success-light text-success"       :
          status === "running" ? "bg-brand-light text-brand"           :
                                 "bg-gray-100 text-ink-subtle"
        }`}
      >
        {status === "done"
          ? <HiOutlineCheckCircle className="h-4 w-4" />
          : <Icon className="h-4 w-4" />
        }
      </span>

      {/* Name + status */}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-ink">{name}</p>
        <div className="mt-0.5 flex items-center gap-2">
          {status === "done" && (
            <span className="text-xs text-success">Terminé</span>
          )}
          {status === "running" && (
            <>
              <span className="text-xs font-semibold text-brand">En cours</span>
              <div className="h-1 max-w-[72px] flex-1 overflow-hidden rounded-full bg-brand-border">
                <div className="h-full w-[45%] animate-progress-bar rounded-full bg-brand" />
              </div>
            </>
          )}
          {status === "waiting" && (
            <span className="flex items-center gap-1 text-xs text-ink-subtle">
              <HiOutlineClock className="h-3 w-3" /> En attente
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/** Agent feature card in the "Nos agents" section */
function AgentCard({ Icon, name, description }) {
  return (
    <div className="group flex flex-col rounded-2xl border border-brand-border bg-white p-6 shadow-card transition-all duration-200 hover:-translate-y-1 hover:border-brand-muted hover:shadow-card-md">
      <div className="mb-4 flex items-start justify-between">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-light text-brand transition-all group-hover:bg-brand group-hover:text-white">
          <Icon className="h-5 w-5" />
        </span>
        <span className="rounded-full bg-brand-light px-2.5 py-0.5 text-xs font-semibold text-brand-darker">
          Module
        </span>
      </div>
      <h3 className="mb-2 text-md font-bold text-ink">{name}</h3>
      <p className="text-sm leading-relaxed text-ink-muted">{description}</p>
    </div>
  );
}

/** "Comment ça marche" step */
function StepCard({ number, title, description }) {
  return (
    <div className="relative z-10 flex flex-1 flex-col items-center px-4 text-center">
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-sm font-extrabold text-white shadow-btn">
        {number}
      </div>
      <h3 className="mb-2 text-md font-bold text-ink">{title}</h3>
      <p className="max-w-[260px] text-sm leading-relaxed text-ink-muted">{description}</p>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Page
───────────────────────────────────────────────────────────────────────────── */
export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className="flex min-h-screen flex-col bg-white font-sans">
      <Navbar variant="landing" />

      <main className="flex-1">

        {/* ── HERO ──────────────────────────────────────────────────────── */}
        <section className="relative overflow-hidden bg-white py-20 md:py-28">
          <BlobBackground opacity={0.35} />

          <div className="relative z-10 mx-auto max-w-6xl px-4 md:px-6">
            <div className="grid gap-12 lg:grid-cols-2 lg:items-center lg:gap-16">

              {/* Left — copy */}
              <div
                className={`transition-all duration-700 ${
                  mounted ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
                }`}
              >
                {/* Tag pill */}
                <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-brand-border bg-brand-light px-4 py-1.5 text-xs font-semibold text-brand-darker">
                  <HiOutlineSparkles className="h-3.5 w-3.5 text-brand" />
                  IA Générative & Agentique
                </span>

                {/* Headline */}
                <h1 className="mb-5 text-5xl font-extrabold leading-[1.1] tracking-tight text-ink md:text-6xl">
                  From idea
                  <br />
                  <span className="bg-gradient-to-r from-brand to-brand-dark bg-clip-text text-transparent">
                    to market
                  </span>
                </h1>

                <p className="mb-8 max-w-lg text-lg leading-relaxed text-ink-muted">
                  Décrivez votre projet. Nos agents IA génèrent l&apos;analyse de marché,
                  l&apos;identité de marque et les contenus en quelques clics.
                </p>

                {/* CTAs */}
                <div className="flex flex-wrap gap-3">
                  <Link
                    to="/register"
                    className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-brand to-brand-dark px-6 py-3 text-sm font-bold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px"
                  >
                    <HiOutlineRocketLaunch className="h-4 w-4" />
                    Lancer mon projet
                  </Link>
                  <Link
                    to="/login"
                    className="inline-flex items-center gap-2 rounded-full border border-brand-border bg-white px-6 py-3 text-sm font-semibold text-ink-body transition-all hover:border-brand-muted hover:text-brand"
                  >
                    Se connecter
                    <HiOutlineArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>

              {/* Right — pipeline preview card */}
              <div
                className={`hidden transition-all duration-700 delay-200 lg:block ${
                  mounted ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
                }`}
              >
                <div className="rounded-2xl border border-brand-border bg-white p-5 shadow-card-lg">
                  <p className="mb-4 text-xs font-bold uppercase tracking-widest text-brand-muted">
                    Pipeline IA — aperçu
                  </p>
                  <div className="space-y-2">
                    {AGENTS_PREVIEW.map((agent) => (
                      <AgentPreviewRow key={agent.id} {...agent} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── AGENTS SECTION ────────────────────────────────────────────── */}
        <section className="bg-brand-50 py-20 md:py-24">
          <div className="mx-auto max-w-6xl px-4 md:px-6">

            <div className="mb-12 text-center">
              <h2 className="mb-3 text-3xl font-extrabold text-ink md:text-4xl">
                Nos agents IA travaillent pour vous
              </h2>
              <p className="mx-auto max-w-lg text-base text-ink-muted">
                Un pipeline intelligent qui transforme votre idée en marque complète, étape par étape.
              </p>
            </div>

            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {AGENTS_CARDS.map((agent) => (
                <AgentCard key={agent.name} {...agent} />
              ))}
            </div>

            {/* Marketing strategy highlight banner */}
            <div className="mt-8 flex flex-col gap-6 rounded-2xl border border-brand-border bg-white p-6 shadow-card md:flex-row md:items-center md:justify-between md:px-8">
              <div className="flex items-center gap-5">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-light text-brand">
                  <HiOutlineChartBarSquare className="h-6 w-6" />
                </span>
                <div>
                  <h3 className="mb-1 text-md font-bold text-ink">Stratégie marketing complète</h3>
                  <p className="text-sm text-ink-muted">
                    Positionnement, personas, canaux prioritaires et plan de lancement go-to-market structuré.
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {MARKETING_TAGS.map(({ Icon, label }) => (
                  <span
                    key={label}
                    className="inline-flex items-center gap-1.5 rounded-full border border-brand-border bg-brand-light px-3.5 py-1.5 text-xs font-semibold text-brand-darker"
                  >
                    <Icon className="h-3.5 w-3.5 text-brand" />
                    {label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── HOW IT WORKS ──────────────────────────────────────────────── */}
        <section className="bg-white py-20 md:py-24">
          <div className="mx-auto max-w-6xl px-4 md:px-6">

            <div className="mb-14 text-center">
              <h2 className="mb-3 text-3xl font-extrabold text-ink md:text-4xl">
                Comment ça marche ?
              </h2>
              <p className="mx-auto max-w-lg text-base text-ink-muted">
                3 étapes simples pour transformer votre idée en marque complète.
              </p>
            </div>

            {/* Desktop steps */}
            <div className="relative hidden md:flex items-start justify-between">
              {/* Dashed connector */}
              <div
                className="absolute top-7 border-t-2 border-dashed border-brand-border"
                style={{ left: "16.666%", right: "16.666%" }}
                aria-hidden
              />
              {STEPS.map((step) => (
                <StepCard key={step.number} {...step} />
              ))}
            </div>

            {/* Mobile steps */}
            <div className="flex flex-col gap-8 md:hidden">
              {STEPS.map((step) => (
                <div key={step.number} className="flex gap-5 text-left">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-sm font-extrabold text-white shadow-btn">
                    {step.number}
                  </div>
                  <div>
                    <h3 className="mb-1 text-md font-bold text-ink">{step.title}</h3>
                    <p className="text-sm leading-relaxed text-ink-muted">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA BANNER ────────────────────────────────────────────────── */}
        <section className="bg-brand-50 py-16">
          <div className="mx-auto max-w-2xl px-4 text-center">
            <h2 className="mb-3 text-3xl font-extrabold text-ink">
              Prêt à lancer votre marque ?
            </h2>
            <p className="mb-8 text-base text-ink-muted">
              Créez votre compte gratuitement et obtenez votre première analyse de marque en quelques minutes.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-brand to-brand-dark px-8 py-3.5 text-sm font-bold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px"
            >
              <HiOutlineRocketLaunch className="h-4 w-4" />
              Commencer gratuitement
            </Link>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
