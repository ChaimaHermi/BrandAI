import { useCallback, useEffect, useState } from "react";
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

const SK_META_PAGES = "brandai_content_meta_pages";
const SK_META_USER = "brandai_content_meta_user_token";
const SK_LI_TOKEN = "brandai_content_linkedin_token";
const SK_LI_URN = "brandai_content_linkedin_urn";
const SK_META_PAGE_ID = "brandai_content_selected_page_id";

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
          window.alert(`Meta : ${p.error}`);
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
          window.alert(`LinkedIn : ${p.error}`);
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
    try {
      const { url } = await fetchMetaOAuthUrl();
      const w = window.open(url, "brandai_meta_oauth", OAUTH_POPUP_FEATURES);
      if (!w) {
        setConnectBusy(null);
        window.alert("Autorisez les fenêtres popup pour vous connecter à Meta.");
      }
    } catch (e) {
      setConnectBusy(null);
      window.alert(e?.message || "OAuth Meta indisponible.");
    }
  }, []);

  const openLinkedInConnect = useCallback(async () => {
    setConnectBusy("linkedin");
    try {
      const { url } = await fetchLinkedInOAuthUrl();
      const w = window.open(url, "brandai_li_oauth", OAUTH_POPUP_FEATURES);
      if (!w) {
        setConnectBusy(null);
        window.alert("Autorisez les fenêtres popup pour vous connecter à LinkedIn.");
      }
    } catch (e) {
      setConnectBusy(null);
      window.alert(e?.message || "OAuth LinkedIn indisponible.");
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
