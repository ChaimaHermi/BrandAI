import { FaFacebookF, FaInstagram, FaLinkedinIn } from "react-icons/fa";

export const PLATFORM_ORDER = ["facebook", "instagram", "linkedin"];

export const PLATFORMS = {
  facebook: {
    key: "facebook",
    label: "Facebook",
    Icon: FaFacebookF,
    color: "#1877F2",
    lightBg: "bg-[#1877F2]/10",
    lightText: "text-[#1877F2]",
    border: "border-[#1877F2]/30",
    activeStyle: { background: "#1877F2", borderColor: "#1877F2" },
    inactiveStyle: { background: "rgba(24,119,242,.07)", borderColor: "rgba(24,119,242,.35)", color: "#1877F2" },
  },
  instagram: {
    key: "instagram",
    label: "Instagram",
    Icon: FaInstagram,
    color: "#E1306C",
    lightBg: "bg-[#E1306C]/10",
    lightText: "text-[#E1306C]",
    border: "border-[#E1306C]/30",
    activeStyle: { background: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)", borderColor: "transparent" },
    inactiveStyle: { background: "linear-gradient(135deg,rgba(131,58,180,.08),rgba(225,48,108,.08),rgba(252,176,69,.08))", borderColor: "rgba(225,48,108,.35)", color: "#C2185B" },
  },
  linkedin: {
    key: "linkedin",
    label: "LinkedIn",
    Icon: FaLinkedinIn,
    color: "#0A66C2",
    lightBg: "bg-[#0A66C2]/10",
    lightText: "text-[#0A66C2]",
    border: "border-[#0A66C2]/30",
    activeStyle: { background: "#0A66C2", borderColor: "#0A66C2" },
    inactiveStyle: { background: "rgba(10,102,194,.07)", borderColor: "rgba(10,102,194,.35)", color: "#0A66C2" },
  },
};

export const KPI_CONFIG = [
  {
    key: "followers",
    label: "Abonnés",
    linkedinLabel: "Relations",
    icon: "users",
  },
  {
    key: "engagement_rate",
    label: "Taux d'engagement",
    linkedinLabel: "Engagement moyen / post",
    icon: "activity",
    isPercent: true,
    linkedinIsPercent: false,
  },
  {
    key: "reach",
    label: "Portée",
    icon: "globe",
    hiddenOn: ["linkedin"],
  },
  {
    key: "post_count",
    label: "Publications synchronisées",
    icon: "file",
  },
  {
    key: "total_engagement",
    label: "Engagement total",
    icon: "activity",
  },
  {
    key: "comments",
    label: "Commentaires",
    icon: "file",
    hiddenOn: ["linkedin"],
  },
  {
    key: "clicks",
    label: "Clics",
    icon: "globe",
    hiddenOn: ["instagram", "linkedin"],
  },
  {
    key: "shares",
    label: "Partages",
    icon: "file",
  },
];
