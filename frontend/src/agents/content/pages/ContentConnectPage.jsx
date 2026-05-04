import { useMemo, useState } from "react";
import { FiLink2, FiCheckCircle, FiClock, FiShield } from "react-icons/fi";
import { FaFacebookF, FaInstagram, FaLinkedinIn } from "react-icons/fa";
import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { usePipeline } from "@/context/PipelineContext";
import ConnectSocialModal from "../components/ConnectSocialModal";
import { useSocialPublish } from "../hooks/useSocialPublish";

const contentAgent = AGENTS.find((a) => a.id === "content");

const PLATFORMS = [
  {
    key: "meta",
    label: "Facebook",
    Icon: FaFacebookF,
    headerStyle: { background: "#1877F2" },
    description: "Publiez sur vos Pages Facebook et gérez les accès.",
    note: null,
  },
  {
    key: "instagram",
    label: "Instagram",
    Icon: FaInstagram,
    headerStyle: { background: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)" },
    description: "Profil professionnel lié à votre Page Meta.",
    note: "Prêt automatiquement via Meta",
  },
  {
    key: "linkedin",
    label: "LinkedIn",
    Icon: FaLinkedinIn,
    headerStyle: { background: "#0A66C2" },
    description: "Connexion dédiée pour votre profil ou Page LinkedIn.",
    note: null,
  },
];

function SocialCard({ platform, connected, linkedName }) {
  const { label, Icon, headerStyle, description, note } = platform;
  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card">
      {/* Colored header strip */}
      <div className="flex items-center gap-2.5 px-4 py-3" style={headerStyle}>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/20">
          <Icon className="h-4 w-4 text-white" />
        </div>
        <p className="text-sm font-bold text-white">{label}</p>
        {connected && (
          <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-white/25 px-2 py-0.5 text-[11px] font-bold text-white">
            <FiCheckCircle className="h-3 w-3" />
            Connecté
          </span>
        )}
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-2 p-4">
        <p className="text-xs leading-relaxed text-ink-muted">{description}</p>
        {note && (
          <p className="inline-flex items-center gap-1 text-2xs font-semibold text-brand">
            <FiShield className="h-3 w-3" />
            {note}
          </p>
        )}
        {linkedName && (
          <p className="text-2xs font-semibold text-success">{linkedName}</p>
        )}

        {/* Status pill */}
        <div className="mt-auto pt-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-2xs font-semibold ${
              connected
                ? "bg-success/10 text-success"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                connected ? "bg-success" : "bg-amber-500"
              }`}
            />
            {connected ? "Prêt à publier" : "Non connecté"}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function ContentConnectPage() {
  const { idea } = usePipeline();
  const social = useSocialPublish(idea?.id ?? null);
  const [open, setOpen] = useState(false);

  const allReady = social.metaConnected && social.linkedinConnected;
  const hasIdea = idea?.id != null;

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <AgentPageHeader
        agent={contentAgent}
        subtitle="Content Creator · Connexions sociales"
      />

      {/* Intro banner */}
      <div className="flex items-center gap-3 rounded-2xl border border-brand-border bg-white px-5 py-4 shadow-card">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-light">
          <FiLink2 size={18} className="text-brand" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-ink">Connect Social Media</p>
          <p className="mt-0.5 text-xs text-ink-muted">
            {hasIdea
              ? "Connexions Meta et LinkedIn enregistrées pour ce projet uniquement. Chaque idée peut avoir ses propres pages."
              : "Ouvrez un projet (idée) depuis le pipeline pour associer des comptes sociaux à ce projet."}
          </p>
        </div>
        {allReady && (
          <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-success/10 px-2.5 py-1 text-2xs font-semibold text-success">
            <FiCheckCircle className="h-3.5 w-3.5" />
            Tout prêt
          </span>
        )}
      </div>

      {/* Platform cards */}
      <div className="grid gap-3 md:grid-cols-3">
        <SocialCard
          platform={PLATFORMS[0]}
          connected={social.metaConnected}
        />
        <SocialCard
          platform={PLATFORMS[1]}
          connected={social.instagramConnected}
        />
        <SocialCard
          platform={PLATFORMS[2]}
          connected={social.linkedinConnected}
          linkedName={social.linkedinName || null}
        />
      </div>

      {/* CTA bar */}
      <Card padding="p-4" className="shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            {allReady ? (
              <>
                <FiCheckCircle className="h-4 w-4 text-success" />
                Toutes les plateformes sont prêtes à publier.
              </>
            ) : (
              <>
                <FiClock className="h-4 w-4 text-brand" />
                Connectez vos comptes pour activer la publication automatique.
              </>
            )}
          </div>
          <Button
            type="button"
            variant="secondary"
            size="md"
            disabled={!hasIdea}
            onClick={() => setOpen(true)}
          >
            <FiLink2 className="h-3.5 w-3.5" />
            Gérer les connexions
          </Button>
        </div>
      </Card>

      <ConnectSocialModal open={open} onClose={() => setOpen(false)} social={social} />
    </div>
  );
}
