import { useCallback, useEffect, useState } from "react";
import { toast } from "react-toastify";
import {
  AI_ORIGIN,
  fetchLinkedInOAuthUrl,
  fetchMetaOAuthUrl,
  postPublishFacebook,
  postPublishInstagram,
  postPublishLinkedIn,
} from "../api/socialPublish.api";
import { PLATFORMS } from "../constants";

/**
 * Le callback OAuth peut être servi sur un autre port que l’API (ex. proxy 8766 → 8001).
 * postMessage envoie alors ev.origin = http://localhost:8766, pas 8001 — il faut accepter les deux.
 */
function isTrustedSocialOAuthOrigin(origin) {
  if (origin === AI_ORIGIN) return true;
  try {
    const u = new URL(origin);
    const api = new URL(AI_ORIGIN);
    if (u.protocol !== api.protocol) return false;
    if (u.hostname !== "localhost" && u.hostname !== "127.0.0.1") return false;
    return true;
  } catch {
    return false;
  }
}

/** Sans noopener : le callback OAuth doit pouvoir utiliser window.opener.postMessage. */
const OAUTH_POPUP_FEATURES = "width=600,height=720,scrollbars=yes";

/** Messages Meta / LinkedIn quand l'utilisateur annule, choisit « plus tard » ou ferme la fenêtre. */
function metaOAuthFeedback(rawError, oauthError) {
  const errCode = String(oauthError || "").toLowerCase();
  if (errCode === "access_denied") {
    return {
      level: "warning",
      message:
        "Connexion interrompue (vous avez choisi « plus tard », refusé l’accès ou fermé la fenêtre). Réessayez avec « Continuer avec Facebook » lorsque vous voulez associer Brand AI à votre compte.",
    };
  }
  const s = String(rawError || "").toLowerCase();
  if (
    s.includes("access_denied") ||
    s.includes("access denied") ||
    s.includes("user denied") ||
    s.includes("cancelled") ||
    s.includes("canceled")
  ) {
    return {
      level: "warning",
      message:
        "Connexion interrompue (vous avez choisi « plus tard », refusé l’accès ou fermé la fenêtre). Réessayez avec « Continuer avec Facebook » lorsque vous voulez associer Brand AI à votre compte.",
    };
  }
  if (
    s.includes("state invalide") ||
    s.includes("expiré") ||
    (s.includes("invalid") && s.includes("state"))
  ) {
    return {
      level: "warning",
      message:
        "Session OAuth expirée. Cliquez de nouveau sur « Continuer avec Facebook ».",
    };
  }
  if (s.includes("code ou state manquant")) {
    return {
      level: "warning",
      message:
        "Connexion incomplète. Réessayez avec « Continuer avec Facebook ».",
    };
  }
  return { level: "error", message: String(rawError || "Erreur inconnue") };
}

function linkedinOAuthFeedback(rawError, oauthError) {
  if (String(oauthError || "").toLowerCase() === "access_denied") {
    return {
      level: "warning",
      message:
        "Connexion LinkedIn interrompue. Réessayez avec « Continuer avec LinkedIn » quand vous êtes prêt.",
    };
  }
  const s = String(rawError || "").toLowerCase();
  if (
    s.includes("access_denied") ||
    s.includes("user_cancelled") ||
    s.includes("user canceled") ||
    s.includes("cancelled")
  ) {
    return {
      level: "warning",
      message:
        "Connexion LinkedIn interrompue. Réessayez avec « Continuer avec LinkedIn » quand vous êtes prêt.",
    };
  }
  if (s.includes("state invalide") || s.includes("expiré")) {
    return {
      level: "warning",
      message: "Session expirée. Relancez « Continuer avec LinkedIn ».",
    };
  }
  return { level: "error", message: String(rawError || "Erreur inconnue") };
}

const SK_META_PAGES = "brandai_content_meta_pages";
const SK_META_USER = "brandai_content_meta_user_token";
const SK_LI_TOKEN = "brandai_content_linkedin_token";
const SK_LI_URN = "brandai_content_linkedin_urn";
const SK_META_PAGE_ID = "brandai_content_selected_page_id";

const SOCIAL_PUBLISH_SESSION_KEYS = [
  SK_META_PAGES,
  SK_META_USER,
  SK_LI_TOKEN,
  SK_LI_URN,
  SK_META_PAGE_ID,
];

/** À appeler à la déconnexion utilisateur : évite de réutiliser Meta/LinkedIn d’une session précédente. */
export function clearSocialPublishSessionStorage() {
  try {
    for (const k of SOCIAL_PUBLISH_SESSION_KEYS) {
      sessionStorage.removeItem(k);
    }
  } catch {
    /* ignore (navigation privée stricte, etc.) */
  }
}

function loadJson(key, fallback) {
  try {
    const s = sessionStorage.getItem(key);
    return s ? JSON.parse(s) : fallback;
  } catch {
    return fallback;
  }
}

/**
 * Connexion OAuth (popup) + publication par plateforme.
 */
export function useSocialPublish() {
  const [metaPages, setMetaPages] = useState(() => loadJson(SK_META_PAGES, []));
  const [metaUserToken, setMetaUserToken] = useState(
    () => sessionStorage.getItem(SK_META_USER) || "",
  );
  const [selectedPageId, setSelectedPageId] = useState(
    () => sessionStorage.getItem(SK_META_PAGE_ID) || "",
  );
  const [linkedinToken, setLinkedinToken] = useState(
    () => sessionStorage.getItem(SK_LI_TOKEN) || "",
  );
  const [linkedinUrn, setLinkedinUrn] = useState(
    () => sessionStorage.getItem(SK_LI_URN) || "",
  );
  const [linkedinName, setLinkedinName] = useState("");
  const [connectBusy, setConnectBusy] = useState(null);

  useEffect(() => {
    sessionStorage.setItem(SK_META_PAGES, JSON.stringify(metaPages));
  }, [metaPages]);
  useEffect(() => {
    if (metaUserToken) sessionStorage.setItem(SK_META_USER, metaUserToken);
    else sessionStorage.removeItem(SK_META_USER);
  }, [metaUserToken]);
  useEffect(() => {
    if (selectedPageId) sessionStorage.setItem(SK_META_PAGE_ID, selectedPageId);
    else sessionStorage.removeItem(SK_META_PAGE_ID);
  }, [selectedPageId]);
  useEffect(() => {
    if (linkedinToken) sessionStorage.setItem(SK_LI_TOKEN, linkedinToken);
    else sessionStorage.removeItem(SK_LI_TOKEN);
  }, [linkedinToken]);
  useEffect(() => {
    if (linkedinUrn) sessionStorage.setItem(SK_LI_URN, linkedinUrn);
    else sessionStorage.removeItem(SK_LI_URN);
  }, [linkedinUrn]);

  useEffect(() => {
    function onMessage(ev) {
      if (!isTrustedSocialOAuthOrigin(ev.origin)) return;
      const p = ev.data;
      if (!p || typeof p !== "object") return;
      if (p.type === "brandai-meta-oauth") {
        setConnectBusy(null);
        if (!p.ok && p.error) {
          const fb = metaOAuthFeedback(p.error, p.oauth_error);
          if (fb.level === "warning") toast.warning(fb.message);
          else toast.error(`Connexion Meta échouée : ${fb.message}`);
          return;
        }
        if (p.ok && Array.isArray(p.pages)) {
          setMetaPages(p.pages);
          if (p.user_access_token) setMetaUserToken(p.user_access_token);
          if (p.pages.length === 1) setSelectedPageId(String(p.pages[0].id));
        }
      }
      if (p.type === "brandai-linkedin-oauth") {
        setConnectBusy(null);
        if (!p.ok && p.error) {
          const fb = linkedinOAuthFeedback(p.error, p.oauth_error);
          if (fb.level === "warning") toast.warning(fb.message);
          else toast.error(`Connexion LinkedIn échouée : ${fb.message}`);
          return;
        }
        if (p.ok && p.access_token) {
          setLinkedinToken(p.access_token);
          if (p.person_urn) setLinkedinUrn(p.person_urn);
          if (p.name) setLinkedinName(String(p.name));
        }
      }
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  const openMetaConnect = useCallback(async () => {
    setConnectBusy("meta");
    let poll;
    try {
      const { url } = await fetchMetaOAuthUrl();
      // Nom unique : évite une popup réutilisée bloquée sur un ancien écran Facebook.
      const w = window.open(
        url,
        `brandai_meta_oauth_${Date.now()}`,
        OAUTH_POPUP_FEATURES,
      );
      if (!w) {
        setConnectBusy(null);
        toast.warning("Popup bloquée — autorisez les fenêtres popup pour vous connecter à Meta.");
        return;
      }
      poll = setInterval(() => {
        if (w.closed) {
          clearInterval(poll);
          setConnectBusy(null);
        }
      }, 400);
    } catch (e) {
      if (poll) clearInterval(poll);
      setConnectBusy(null);
      toast.error(e?.message || "OAuth Meta indisponible.");
    }
  }, []);

  const openLinkedInConnect = useCallback(async () => {
    setConnectBusy("linkedin");
    let poll;
    try {
      const { url } = await fetchLinkedInOAuthUrl();
      const w = window.open(
        url,
        `brandai_li_oauth_${Date.now()}`,
        OAUTH_POPUP_FEATURES,
      );
      if (!w) {
        setConnectBusy(null);
        toast.warning("Popup bloquée — autorisez les fenêtres popup pour vous connecter à LinkedIn.");
        return;
      }
      poll = setInterval(() => {
        if (w.closed) {
          clearInterval(poll);
          setConnectBusy(null);
        }
      }, 400);
    } catch (e) {
      if (poll) clearInterval(poll);
      setConnectBusy(null);
      toast.error(e?.message || "OAuth LinkedIn indisponible.");
    }
  }, []);

  const selectedPage = metaPages.find((p) => String(p.id) === String(selectedPageId)) || null;

  const publishToPlatform = useCallback(
    async (platform, { caption, imageUrl }) => {
      const text = (caption || "").trim();
      if (!text) throw new Error("Aucun texte à publier.");

      if (platform === PLATFORMS.facebook) {
        if (!selectedPage?.access_token || !selectedPage?.id) {
          throw new Error("Connectez Meta et choisissez une Page Facebook.");
        }
        return postPublishFacebook({
          message: text,
          page_id: String(selectedPage.id),
          page_access_token: selectedPage.access_token,
          link: imageUrl && imageUrl.startsWith("https") ? imageUrl : undefined,
        });
      }

      if (platform === PLATFORMS.instagram) {
        if (!imageUrl || !imageUrl.startsWith("https")) {
          throw new Error("Instagram exige une image (URL HTTPS, ex. Cloudinary). Générez un post avec image.");
        }
        if (!selectedPage?.access_token || !selectedPage?.id) {
          throw new Error("Connectez Meta et choisissez la Page liée au compte Instagram pro.");
        }
        return postPublishInstagram({
          caption: text,
          image_url: imageUrl,
          page_id: String(selectedPage.id),
          page_access_token: selectedPage.access_token,
        });
      }

      if (platform === PLATFORMS.linkedin) {
        if (!linkedinToken) {
          throw new Error("Connectez LinkedIn d’abord.");
        }
        return postPublishLinkedIn({
          message: text,
          access_token: linkedinToken,
          person_urn: linkedinUrn || undefined,
          image_url:
            imageUrl && imageUrl.startsWith("https") ? imageUrl : undefined,
        });
      }

      throw new Error("Plateforme non supportée.");
    },
    [selectedPage, linkedinToken, linkedinUrn],
  );

  return {
    metaPages,
    selectedPageId,
    setSelectedPageId,
    selectedPage,
    metaConnected: metaPages.length > 0,
    linkedinConnected: Boolean(linkedinToken),
    linkedinName: linkedinName || null,
    connectBusy,
    openMetaConnect,
    openLinkedInConnect,
    publishToPlatform,
    disconnectMeta: useCallback(() => {
      setMetaPages([]);
      setMetaUserToken("");
      setSelectedPageId("");
      sessionStorage.removeItem(SK_META_PAGES);
      sessionStorage.removeItem(SK_META_USER);
      sessionStorage.removeItem(SK_META_PAGE_ID);
    }, []),
    disconnectLinkedIn: useCallback(() => {
      setLinkedinToken("");
      setLinkedinUrn("");
      setLinkedinName("");
      sessionStorage.removeItem(SK_LI_TOKEN);
      sessionStorage.removeItem(SK_LI_URN);
    }, []),
  };
}
