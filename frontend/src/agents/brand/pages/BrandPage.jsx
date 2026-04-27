import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "react-toastify";
import { FiLayers } from "react-icons/fi";
import { usePipeline } from "@/context/PipelineContext";
import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import {
  buildLegacyRecordFromBundle,
  fetchBrandingBundle,
  hasSavedBrandIdentityPreview,
  generateBrandNames,
  generateLogo,
  generatePalettes,
  generateSlogans,
  patchBrandKit,
  patchLogoResult,
  patchNamingResult,
  patchPaletteResult,
  patchSloganResult,
  patchIdeaPipelineProgress,
} from "../api/brandIdentity.api";
import AboutProjectCard from "../components/AboutProjectCard";
import SectionHeader from "../components/SectionHeader";
import BrandStepper from "../components/BrandStepper";
import FinalBrandPreview from "../components/FinalBrandPreview";
import NamingStep from "../components/steps/NamingStep";
import SloganStep from "../components/steps/SloganStep";
import PaletteStep from "../components/steps/PaletteStep";
import LogoStep from "../components/steps/LogoStep";
import "../styles/brandStudio.css";

const brandWizardStorageKey = (ideaId) =>
  ideaId != null ? `brand_wizard_${ideaId}` : "";

/** Labels stepper — projet → naming → slogan → couleurs → logo → aperçu final */
const STEPS = ["Projet", "Naming", "Slogan", "Couleurs", "Logo", "Aperçu"];
const brandAgent = AGENTS.find((a) => a.id === "brand");

const initialStyleTon = () => ({
  brandValues: [],
  personality: [],
  userFeelings: [],
});

const initialConstraints = () => ({
  nameLanguage: "fr",
  nameLength: "medium",
  includeKeywords: "",
  excludeKeywords: "",
});

function buildGeneratePayload(ideaId, styleTon, constraints) {
  return {
    idea_id: ideaId,
    style_ton: {
      brand_values: styleTon.brandValues,
      personality: styleTon.personality,
      user_feelings: styleTon.userFeelings,
    },
    constraints: {
      name_language: constraints.nameLanguage,
      name_length: constraints.nameLength,
      include_keywords: constraints.includeKeywords.trim(),
      exclude_keywords: constraints.excludeKeywords.trim(),
    },
  };
}

const initialSloganForm = () => ({
  positionnement: "",
  sloganStyleTones: [],
  messageUsp: [],
  sloganFormats: [],
  styleLinguistique: [],
  longueur: "",
  langue: "",
  motsEviter: "",
});

function buildSloganPayload(ideaId, brandName, form) {
  return {
    idea_id: ideaId,
    brand_name: brandName,
    positionnement: form.positionnement,
    style_ton_slogan: form.sloganStyleTones,
    message_usp: form.messageUsp,
    format: form.sloganFormats,
    style_linguistique: form.styleLinguistique,
    longueur: form.longueur,
    langue: form.langue,
    mots_eviter: form.motsEviter.trim(),
  };
}

export default function BrandPage() {
  const { idea, token, refetch: refetchIdea } = usePipeline();
  const [record, setRecord] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [savingFinal, setSavingFinal] = useState(false);
  const [styleTon, setStyleTon] = useState(initialStyleTon);
  const [constraints, setConstraints] = useState(initialConstraints);
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastMockMessage, setLastMockMessage] = useState("");
  const [step, setStep] = useState(0);
  const [animKey, setAnimKey] = useState(0);

  const [chosenBrandName, setChosenBrandName] = useState(null);
  const [sloganForm, setSloganForm] = useState(initialSloganForm);
  const [generatedSlogans, setGeneratedSlogans] = useState([]);
  const [isGeneratingSlogans, setIsGeneratingSlogans] = useState(false);
  const [sloganGenMessage, setSloganGenMessage] = useState("");
  const [selectedSlogan, setSelectedSlogan] = useState("");
  const [selectedPaletteId, setSelectedPaletteId] = useState(null);
  const [generatedPaletteOptions, setGeneratedPaletteOptions] = useState([]);
  const [isGeneratingPalettes, setIsGeneratingPalettes] = useState(false);
  const [paletteGenMessage, setPaletteGenMessage] = useState("");
  const [generatedLogoConcepts, setGeneratedLogoConcepts] = useState([]);
  const [isGeneratingLogo, setIsGeneratingLogo] = useState(false);
  const [logoGenMessage, setLogoGenMessage] = useState("");

  /** Évite de réappliquer l’atterrissage (aperçu / assistant) à chaque refetch. */
  const appliedLandingForIdeaRef = useRef(null);

  useEffect(() => {
    refetchIdea?.();
  }, [idea?.id, refetchIdea]);

  useEffect(() => {
    appliedLandingForIdeaRef.current = null;
    setStep(0);
    setChosenBrandName(null);
    setSloganForm(initialSloganForm());
    setGeneratedSlogans([]);
    setSloganGenMessage("");
    setSelectedSlogan("");
    setGeneratedPaletteOptions([]);
    setSelectedPaletteId(null);
    setPaletteGenMessage("");
    setGeneratedLogoConcepts([]);
    setLogoGenMessage("");
    setAnimKey((k) => k + 1);
  }, [idea?.id]);

  const refetchBrandRecord = useCallback(async () => {
    if (!idea?.id || !token) {
      setRecord(null);
      return;
    }
    setLoadError("");
    try {
      const b = await fetchBrandingBundle(idea.id, token);
      setRecord(buildLegacyRecordFromBundle(idea.id, b));
      if (b?.naming?.chosen_name) {
        setChosenBrandName(b.naming.chosen_name);
      }
      if (b?.slogan?.chosen_slogan) {
        setSelectedSlogan(b.slogan.chosen_slogan);
      }
    } catch (e) {
      setLoadError(e?.message || "Chargement impossible");
    }
  }, [idea?.id, token]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!idea?.id || !token) {
        if (!cancelled) setRecord(null);
        return;
      }
      setLoadError("");
      try {
        const b = await fetchBrandingBundle(idea.id, token);
        if (cancelled) return;
        setRecord(buildLegacyRecordFromBundle(idea.id, b));
        if (b?.naming?.chosen_name) {
          setChosenBrandName(b.naming.chosen_name);
        }
        if (b?.slogan?.chosen_slogan) {
          setSelectedSlogan(b.slogan.chosen_slogan);
        }
        if (appliedLandingForIdeaRef.current !== idea.id) {
          appliedLandingForIdeaRef.current = idea.id;
          const wKey = brandWizardStorageKey(idea.id);
          if (wKey && sessionStorage.getItem(wKey) === "1") {
            setStep(0);
          } else if (hasSavedBrandIdentityPreview(b)) {
            setStep(5);
            setAnimKey((k) => k + 1);
          }
        }
      } catch (e) {
        if (!cancelled) setLoadError(e?.message || "Chargement impossible");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [idea?.id, token]);

  const brand = useMemo(() => record?.result_json || null, [record]);
  const names = Array.isArray(brand?.name_options) ? brand.name_options : [];
  const status = brand?.branding_status;
  const errors = brand?.agent_errors || {};
  const hasNamingResults = names.length > 0;
  const persistedSloganOpts = Array.isArray(brand?.slogan_options)
    ? brand.slogan_options
    : [];
  const hasSloganResults =
    generatedSlogans.length > 0 || persistedSloganOpts.length > 0;

  const persistedPaletteOpts = Array.isArray(brand?.palette_options)
    ? brand.palette_options
    : [];
  const hasPaletteResults =
    generatedPaletteOptions.length > 0 || persistedPaletteOpts.length > 0;

  const paletteListDisplayed = useMemo(() => {
    if (generatedPaletteOptions.length > 0) return generatedPaletteOptions;
    return persistedPaletteOpts;
  }, [generatedPaletteOptions, persistedPaletteOpts]);

  const sloganListDisplayed = useMemo(() => {
    if (generatedSlogans.length > 0) return generatedSlogans;
    return persistedSloganOpts
      .map((o) => (typeof o === "string" ? o : o?.text || ""))
      .filter(Boolean);
  }, [generatedSlogans, persistedSloganOpts]);

  const persistedLogoConcepts = Array.isArray(brand?.logo_concepts)
    ? brand.logo_concepts
    : [];

  const logoConceptsDisplayed = useMemo(() => {
    if (generatedLogoConcepts.length > 0) return generatedLogoConcepts;
    return persistedLogoConcepts;
  }, [generatedLogoConcepts, persistedLogoConcepts]);

  const logoPreviewUrl = useMemo(() => {
    const c0 = logoConceptsDisplayed[0];
    if (c0?.image_base64 && c0?.image_mime) {
      return `data:${c0.image_mime};base64,${c0.image_base64}`;
    }
    return null;
  }, [logoConceptsDisplayed]);

  const logoPreviewTransparentUrl = useMemo(() => {
    const c0 = logoConceptsDisplayed[0];
    if (c0?.image_base64_transparent && c0?.image_mime_transparent) {
      return `data:${c0.image_mime_transparent};base64,${c0.image_base64_transparent}`;
    }
    return null;
  }, [logoConceptsDisplayed]);

  useEffect(() => {
    if (!idea?.id || !record?.result_json || record.idea_id !== idea.id) {
      return;
    }
    const opts = record.result_json.slogan_options;
    if (!Array.isArray(opts) || opts.length === 0) return;
    const texts = opts
      .map((o) => (typeof o === "string" ? o : o?.text || ""))
      .filter(Boolean);
    if (texts.length === 0) return;
    setGeneratedSlogans((prev) => (prev.length > 0 ? prev : texts));
  }, [idea?.id, record?.idea_id, record?.result_json]);

  useEffect(() => {
    if (!idea?.id || !record?.result_json || record.idea_id !== idea.id) {
      return;
    }
    const opts = record.result_json.palette_options;
    if (!Array.isArray(opts) || opts.length === 0) return;
    setGeneratedPaletteOptions((prev) => (prev.length > 0 ? prev : opts));
  }, [idea?.id, record?.idea_id, record?.result_json]);

  useEffect(() => {
    if (!idea?.id || !record?.result_json || record.idea_id !== idea.id) {
      return;
    }
    const lc = record.result_json.logo_concepts;
    if (!Array.isArray(lc) || lc.length === 0) return;
    setGeneratedLogoConcepts((prev) => (prev.length > 0 ? prev : lc));
  }, [idea?.id, record?.idea_id, record?.result_json]);

  const displayBrandName = useMemo(
    () =>
      chosenBrandName ||
      names[0]?.name ||
      idea?.name ||
      "Votre marque",
    [chosenBrandName, names, idea?.name],
  );

  /** Texte « pourquoi ce nom » : aligné sur l’option naming choisie (description / rationale). */
  const selectedNameWhyText = useMemo(() => {
    const target = (displayBrandName || "").trim().toLowerCase();
    if (!target || !names.length) return "";
    const opt = names.find(
      (o) =>
        typeof o?.name === "string" && o.name.trim().toLowerCase() === target,
    );
    const raw = (opt?.rationale || opt?.description || "").trim();
    return raw;
  }, [names, displayBrandName]);

  useEffect(() => {
    if (paletteListDisplayed.length === 0) return;
    setSelectedPaletteId((prev) => (prev == null ? "p-0" : prev));
  }, [paletteListDisplayed]);

  const canGenerate = Boolean(idea?.id && token);

  const handleGenerate = useCallback(async (opts = {}) => {
    if (!idea?.id || !token) return { ok: false };
    const userRemarks =
      typeof opts.userRemarks === "string" ? opts.userRemarks.trim() : "";
    const fromRegeneratePopup = Boolean(opts.fromRegeneratePopup);
    const payload = buildGeneratePayload(idea.id, styleTon, constraints);
    setIsGenerating(true);
    setLastMockMessage("");
    try {
      const result = await generateBrandNames(idea.id, token, {
        style_ton: payload.style_ton,
        constraints: payload.constraints,
        user_remarks: userRemarks,
      });
      if (import.meta.env.DEV) {
        console.info("[brand] naming result", result);
      }
      if (result.status !== "name_generated") {
        const err =
          result.name_error ||
          (Array.isArray(result.errors) && result.errors.length
            ? result.errors.join(" ")
            : null) ||
          "La génération de noms n'a pas abouti.";
        setLastMockMessage(err);
        toast.error(err);
        return { ok: false };
      }
      if (fromRegeneratePopup) {
        const msg = result.persisted
          ? "Régénération réussie — nouveaux noms enregistrés."
          : "Régénération réussie — vérifiez la sauvegarde si besoin.";
        setLastMockMessage(msg);
        toast.success(msg);
      } else {
        const msg = result.persisted
          ? "Noms générés et enregistrés."
          : "Noms générés (la sauvegarde a peut-être échoué).";
        setLastMockMessage(msg);
        toast.success(msg);
      }
      await refetchBrandRecord();
      return { ok: true };
    } catch (e) {
      const errMsg = e?.message || "Erreur réseau ou serveur IA.";
      setLastMockMessage(errMsg);
      toast.error(errMsg);
      return { ok: false };
    } finally {
      setIsGenerating(false);
    }
  }, [idea?.id, token, styleTon, constraints, refetchBrandRecord]);

  const handleGenerateSlogans = useCallback(async (opts = {}) => {
    if (!idea?.id || !token) return { ok: false };
    const userRemarks =
      typeof opts.userRemarks === "string" ? opts.userRemarks.trim() : "";
    const fromRegeneratePopup = Boolean(opts.fromRegeneratePopup);
    const payload = buildSloganPayload(idea.id, displayBrandName, sloganForm);
    setIsGeneratingSlogans(true);
    setSloganGenMessage("");
    try {
      if (import.meta.env.DEV) {
        console.info("[brand] slogan payload", payload);
      }
      const result = await generateSlogans(idea.id, token, {
        brand_name: displayBrandName,
        preferences: {
          positionnement: sloganForm.positionnement,
          style_ton_slogan: sloganForm.sloganStyleTones,
          message_usp: sloganForm.messageUsp,
          format: sloganForm.sloganFormats,
          style_linguistique: sloganForm.styleLinguistique,
          longueur: sloganForm.longueur,
          langue: sloganForm.langue,
          mots_eviter: sloganForm.motsEviter.trim(),
          user_remarks: userRemarks,
        },
      });
      const texts = (result.slogan_options || [])
        .map((o) => (typeof o === "string" ? o : o?.text || ""))
        .filter(Boolean);
      setGeneratedSlogans(texts);
      if (result.status !== "slogan_generated") {
        const err = result.slogan_error ||
          (Array.isArray(result.errors) && result.errors.length
            ? result.errors.join(" ")
            : null) ||
          "La génération de slogans n'a pas abouti.";
        setSloganGenMessage(err);
        toast.error(err);
        return { ok: false };
      }
      if (fromRegeneratePopup) {
        const msg = result.persisted
          ? "Régénération réussie — nouveaux slogans enregistrés."
          : "Régénération réussie — vérifiez la sauvegarde si besoin.";
        setSloganGenMessage(msg);
        toast.success(msg);
      } else {
        const msg = result.persisted
          ? "Slogans générés et enregistrés."
          : "Slogans générés (vérifiez la sauvegarde si besoin).";
        setSloganGenMessage(msg);
        toast.success(msg);
      }
      await refetchBrandRecord();
      return { ok: true };
    } catch (e) {
      const errMsg = e?.message || "Erreur réseau ou serveur IA.";
      setSloganGenMessage(errMsg);
      toast.error(errMsg);
      setGeneratedSlogans([]);
      return { ok: false };
    } finally {
      setIsGeneratingSlogans(false);
    }
  }, [idea?.id, token, displayBrandName, sloganForm, refetchBrandRecord]);

  const handleGeneratePalettes = useCallback(async (opts = {}) => {
    if (!idea?.id || !token) return { ok: false };
    const fromRegeneratePopup = Boolean(opts.fromRegeneratePopup);
    setIsGeneratingPalettes(true);
    setPaletteGenMessage("");
    try {
      const result = await generatePalettes(idea.id, token, {
        brand_name: displayBrandName,
      });
      const rawOpts = result.palette_options || [];
      setGeneratedPaletteOptions(Array.isArray(rawOpts) ? rawOpts : []);
      if (result.status !== "palette_generated") {
        const err = result.palette_error ||
          (Array.isArray(result.errors) && result.errors.length
            ? result.errors.join(" ")
            : null) ||
          "La génération de palettes n'a pas abouti.";
        setPaletteGenMessage(err);
        toast.error(err);
        return { ok: false };
      }
      setSelectedPaletteId("p-0");
      if (fromRegeneratePopup) {
        const msg = result.persisted
          ? "Régénération réussie — nouvelles palettes enregistrées."
          : "Régénération réussie — vérifiez la sauvegarde si besoin.";
        setPaletteGenMessage(msg);
        toast.success(msg);
      } else {
        const msg = result.persisted
          ? "Palettes générées et enregistrées."
          : "Palettes générées (vérifiez la sauvegarde si besoin).";
        setPaletteGenMessage(msg);
        toast.success(msg);
      }
      await refetchBrandRecord();
      return { ok: true };
    } catch (e) {
      const errMsg = e?.message || "Erreur réseau ou serveur IA.";
      setPaletteGenMessage(errMsg);
      toast.error(errMsg);
      setGeneratedPaletteOptions([]);
      return { ok: false };
    } finally {
      setIsGeneratingPalettes(false);
    }
  }, [idea?.id, token, displayBrandName, refetchBrandRecord]);

  const handleGenerateLogo = useCallback(async () => {
    if (!idea?.id || !token) return { ok: false };
    if (!displayBrandName) {
      setLogoGenMessage("Choisissez d’abord un nom de marque.");
      return { ok: false };
    }
    setIsGeneratingLogo(true);
    setLogoGenMessage("");
    try {
      const result = await generateLogo(idea.id, token, {
        brand_name: displayBrandName,
        slogan_hint: selectedSlogan || null,
        palette_color_hint: null,
        persist: true,
        persist_image_base64: false,
      });
      if (result.status !== "logo_generated") {
        const err =
          result.logo_error ||
          result.logo_image_error ||
          (Array.isArray(result.errors) && result.errors.length
            ? result.errors.join(" ")
            : null) ||
          "La génération du logo n’a pas abouti.";
        setLogoGenMessage(err);
        toast.error(err);
        return { ok: false };
      }
      const concepts = result.logo_concepts || [];
      setGeneratedLogoConcepts(concepts);
      if (result.logo_image_error) {
        const warnMsg = `Prompt enregistré, mais la génération d’image a échoué : ${result.logo_image_error}`;
        setLogoGenMessage(warnMsg);
        toast.warning(warnMsg);
      } else {
        const c0 = concepts[0];
        const sourceHint = (() => {
          if (c0?.image_provider === "pollinations") return " (Pollinations.AI)";
          if (c0?.image_provider === "huggingface") {
            const im = String(c0?.image_model || "").toLowerCase();
            if (im.includes("qwen")) return " (Qwen via Hugging Face)";
            return " (Hugging Face)";
          }
          return "";
        })();
        const successMsg = concepts.length
          ? `Logo généré${sourceHint}. Vous pouvez passer à l’aperçu final.`
          : "Réponse reçue sans image.";
        setLogoGenMessage(successMsg);
        if (concepts.length) toast.success(`Logo généré${sourceHint} !`);
      }
      await refetchBrandRecord();
      return { ok: true };
    } catch (e) {
      const errMsg = e?.message || "Erreur réseau ou serveur IA.";
      setLogoGenMessage(errMsg);
      toast.error(errMsg);
      return { ok: false };
    } finally {
      setIsGeneratingLogo(false);
    }
  }, [idea?.id, token, displayBrandName, selectedSlogan, refetchBrandRecord]);

  const persistFinalChoices = useCallback(async () => {
    if (!idea?.id || !token) return;
    const chosenAt = new Date().toISOString();
    const palettes = paletteListDisplayed;
    let pIdx = 0;
    if (selectedPaletteId && String(selectedPaletteId).startsWith("p-")) {
      pIdx = parseInt(String(selectedPaletteId).slice(2), 10);
    }
    const chosenPalette = palettes[pIdx] ?? null;
    const namePick =
      chosenBrandName ||
      (names[0] && (typeof names[0].name === "string" ? names[0].name : null)) ||
      null;

    await patchNamingResult(idea.id, token, {
      chosen_name: namePick,
      chosen_at: chosenAt,
      status: "validated",
    });
    await patchSloganResult(idea.id, token, {
      chosen_slogan: selectedSlogan || null,
      based_on_name: displayBrandName,
      chosen_at: chosenAt,
      status: "validated",
    });
    await patchPaletteResult(idea.id, token, {
      chosen: chosenPalette,
      chosen_at: chosenAt,
      status: "validated",
    });
    await patchLogoResult(idea.id, token, {
      generated: { logo_concepts: logoConceptsDisplayed },
      chosen_at: chosenAt,
      status: "validated",
    });
    const b = await fetchBrandingBundle(idea.id, token);
    await patchBrandKit(idea.id, token, {
      naming_id: b.naming?.id ?? null,
      slogan_id: b.slogan?.id ?? null,
      palette_id: b.palette?.id ?? null,
      logo_id: b.logo?.id ?? null,
    });
    await patchIdeaPipelineProgress(idea.id, token, {
      brand_identity: {
        status: "completed",
        completed: true,
        completed_at: chosenAt,
        chosen_name: namePick,
        chosen_slogan: selectedSlogan || null,
        logo_preview_url: logoPreviewUrl || null,
      },
    });
    const wKey = brandWizardStorageKey(idea.id);
    if (wKey) sessionStorage.removeItem(wKey);
    await refetchBrandRecord();
    await refetchIdea?.();
    toast.success("Kit de marque enregistré avec succès !");
  }, [
    idea?.id,
    token,
    chosenBrandName,
    names,
    selectedSlogan,
    displayBrandName,
    paletteListDisplayed,
    selectedPaletteId,
    logoConceptsDisplayed,
    logoPreviewUrl,
    refetchBrandRecord,
    refetchIdea,
  ]);

  const canAdvance = useMemo(() => {
    if (step === 0) return Boolean(idea?.id);
    if (step === 1) return Boolean(chosenBrandName && idea?.id);
    if (step === 2) return true;
    if (step === 3) return Boolean(selectedPaletteId && hasPaletteResults);
    if (step === 4) return true;
    return false;
  }, [step, idea?.id, chosenBrandName, selectedPaletteId, hasPaletteResults]);

  async function advance() {
    if (!canAdvance || savingFinal) return;
    if (step === 4) {
      try {
        setSavingFinal(true);
        setLoadError("");
        await persistFinalChoices();
      } catch (e) {
        setLoadError(e?.message || "Impossible d'enregistrer votre kit.");
        setSavingFinal(false);
        return;
      }
      setSavingFinal(false);
    }
    setAnimKey((k) => k + 1);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setAnimKey((k) => k + 1);
    setStep((s) => Math.max(s - 1, 0));
  }

  function restartWizard() {
    if (idea?.id != null) {
      const wKey = brandWizardStorageKey(idea.id);
      if (wKey) sessionStorage.setItem(wKey, "1");
    }
    setAnimKey((k) => k + 1);
    setStep(0);
    setChosenBrandName(null);
    setSloganForm(initialSloganForm());
    setGeneratedSlogans([]);
    setSloganGenMessage("");
    setSelectedSlogan("");
    setGeneratedPaletteOptions([]);
    setSelectedPaletteId(null);
    setPaletteGenMessage("");
    setGeneratedLogoConcepts([]);
    setLogoGenMessage("");
    setStyleTon(initialStyleTon());
    setConstraints(initialConstraints());
    setLastMockMessage("");
  }

  function renderStepContent() {
    return (
      <div key={`${animKey}-${step}`}>
        {step === 0 && (
          <div className="bi-fade-up">
            <SectionHeader
              step={1}
              title="À propos de votre projet"
              sub="Synthèse des informations de votre projet pour démarrer le parcours d’identité."
            />
            <AboutProjectCard idea={idea} embedded />
          </div>
        )}

        {step === 1 && (
          <NamingStep
            styleTon={styleTon}
            onStyleTon={setStyleTon}
            constraints={constraints}
            onConstraints={setConstraints}
            canGenerate={canGenerate}
            isGenerating={isGenerating}
            onGenerate={handleGenerate}
            lastMockMessage={lastMockMessage}
            hasNamingResults={hasNamingResults}
            record={record}
            names={names}
            status={status}
            errors={errors}
            chosenBrandName={chosenBrandName}
            onChooseBrandName={setChosenBrandName}
          />
        )}

        {step === 2 && (
          <SloganStep
            brandName={displayBrandName}
            sloganForm={sloganForm}
            setSloganForm={setSloganForm}
            generatedSlogans={sloganListDisplayed}
            isGeneratingSlogans={isGeneratingSlogans}
            onGenerateSlogans={handleGenerateSlogans}
            hasSloganResults={hasSloganResults}
            sloganGenMessage={sloganGenMessage}
            selectedSlogan={selectedSlogan}
            onSelectSlogan={setSelectedSlogan}
          />
        )}

        {step === 3 && (
          <PaletteStep
            paletteOptions={paletteListDisplayed}
            selectedPaletteId={selectedPaletteId}
            onSelectPalette={setSelectedPaletteId}
            isGeneratingPalettes={isGeneratingPalettes}
            onGeneratePalettes={handleGeneratePalettes}
            paletteGenMessage={paletteGenMessage}
            hasPaletteResults={hasPaletteResults}
            canGenerate={canGenerate && Boolean(displayBrandName)}
            brandNameLabel={displayBrandName}
          />
        )}

        {step === 4 && (
          <LogoStep
            canGenerate={canGenerate && Boolean(displayBrandName)}
            isGeneratingLogo={isGeneratingLogo}
            onGenerateLogo={handleGenerateLogo}
            logoGenMessage={logoGenMessage}
            logoPreviewUrl={logoPreviewUrl}
            logoPreviewTransparentUrl={logoPreviewTransparentUrl}
            logoConcept={logoConceptsDisplayed[0] ?? null}
          />
        )}

        {step === 5 && (
          <FinalBrandPreview
            brandName={displayBrandName}
            sloganText={selectedSlogan}
            paletteOptions={paletteListDisplayed}
            selectedPaletteId={selectedPaletteId}
            logoPreviewUrl={logoPreviewUrl}
            logoPreviewTransparentUrl={logoPreviewTransparentUrl}
            logoConcept={logoConceptsDisplayed[0] ?? null}
            nameWhyText={selectedNameWhyText}
          />
        )}
      </div>
    );
  }

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">

      {/* ── Pipeline step header — même pattern que MarketPage / MarketingPage ── */}
      <AgentPageHeader
        agent={brandAgent}
        subtitle={
          step === 5
            ? "Brand Identity · Aperçu enregistré (vous pouvez recommencer le parcours ci‑dessous)"
            : "Brand Identity · Parcours guidé"
        }
      />

      {/* ── Contenu centré ────────────────────────────────────────────────────── */}
      <div className="bi-studio mx-auto w-full max-w-[860px] flex flex-col gap-3">

        {/* ── Intro card : titre + description + aperçu marque ─────────────── */}
        <div className="rounded-2xl border border-brand-border bg-white px-5 py-4 shadow-card">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-light">
              <FiLayers size={16} className="text-brand" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-extrabold text-ink">Identité de marque</p>
              <p className="mt-0.5 text-xs text-ink-muted">
                {step === 5 ? (
                  <>
                    Aperçu de votre kit enregistré. Utilisez « Retour » pour modifier une étape, ou
                    « Recommencer » pour relancer tout le parcours depuis le début.
                  </>
                ) : (
                  <>
                    Parcours en 6 étapes : projet, naming, slogan, palette, logo généré, puis aperçu
                    final de votre kit.
                  </>
                )}
              </p>
              {(selectedSlogan || chosenBrandName || names[0]) && (
                <div className="mt-2.5 flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-brand/20 bg-brand-light px-2.5 py-0.5 text-xs font-semibold text-brand-darker">
                    {displayBrandName}
                  </span>
                  {selectedSlogan && (
                    <span className="text-xs italic text-ink-muted">
                      &ldquo;{selectedSlogan}&rdquo;
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Stepper ───────────────────────────────────────────────────────── */}
        <BrandStepper steps={STEPS} current={step} />

        {/* ── Erreur de chargement ──────────────────────────────────────────── */}
        {loadError && (
          <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-center text-sm text-red-700">
            {loadError}
          </div>
        )}

        {/* ── Contenu de l'étape ────────────────────────────────────────────── */}
        <div>{renderStepContent()}</div>

        {/* ── Navigation ───────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between gap-3 rounded-2xl border border-brand-border bg-white px-5 py-3 shadow-card">
          <button
            type="button"
            className="bi-btn-outline"
            onClick={back}
            disabled={step === 0}
          >
            ← Retour
          </button>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-ink-subtle">
              {step + 1} / {STEPS.length}
            </span>
            <div className="flex gap-1">
              {STEPS.map((_, i) => (
                <div
                  key={i}
                  className="h-[3px] rounded-[3px] transition-all duration-300"
                  style={{
                    width: i === step ? 18 : 5,
                    background: i <= step ? "var(--brand)" : "var(--brand-border)",
                  }}
                />
              ))}
            </div>
          </div>

          {step < STEPS.length - 1 ? (
            <button
              type="button"
              className="bi-btn-primary"
              onClick={() => advance()}
              disabled={!canAdvance || savingFinal}
            >
              {step === 4 ? "Enregistrer et voir l'aperçu →" : "Continuer →"}
            </button>
          ) : (
            <button
              type="button"
              className="bi-btn-outline"
              onClick={restartWizard}
            >
              Recommencer
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
