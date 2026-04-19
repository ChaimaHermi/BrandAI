"""
Outils LangChain pour SloganAgent (ReAct) : brouillon LLM + validation déterministe.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from config.branding_config import SLOGAN_TARGET_COUNT
from prompts.branding.slogan_prompt import (
    SLOGAN_SYSTEM_PROMPT,
    build_slogan_user_prompt,
)
from tools.branding.palette_tools import parse_llm_json_object

SLOGAN_RATIONALE_MIN_LEN = 12
SLOGAN_TEXT_MAX_LEN = 220


def normalize_slogan_options(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append({"text": item.strip(), "rationale": ""})
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("slogan") or "").strip()
        if not text:
            continue
        rationale = str(item.get("rationale") or item.get("description") or "").strip()
        out.append({"text": text, "rationale": rationale})
    return out


def _slogan_signature(text: str) -> str:
    t = " ".join(str(text or "").lower().split())
    t = re.sub(r"[^\w\sàâäéèêëïîôùûüÿçæœ'-]", "", t, flags=re.IGNORECASE)
    return t.strip()


def _avoid_tokens(prefs: dict | None) -> list[str]:
    if not prefs:
        return []
    raw = prefs.get("mots_eviter")
    if raw is None or str(raw).strip() in ("", "—", "-"):
        return []
    parts = re.split(r"[,;]+", str(raw).lower())
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def _slogans_pairwise_distinct(options: list[dict[str, Any]]) -> bool:
    sigs = [_slogan_signature(o.get("text") or "") for o in options]
    return len(sigs) == len(set(sigs)) and all(sigs)


def _text_has_avoided_phrase(text: str, tokens: list[str]) -> str | None:
    low = str(text).lower()
    for tok in tokens:
        if tok and tok in low:
            return tok
    return None


def make_draft_slogans_tool(
    llm,
    idea: dict,
    brand_name: str,
    preferences: dict | None,
    *,
    target: int = SLOGAN_TARGET_COUNT,
):
    @traceable(name="tool.draft_slogans", tags=["branding", "tool", "slogan_draft"])
    def _draft(validation_feedback: str) -> str:
        user_prompt = build_slogan_user_prompt(
            idea,
            brand_name,
            preferences,
            target=target,
        )
        fb = (validation_feedback or "").strip()
        if fb:
            user_prompt += (
                "\n\n--- RETOUR DU VALIDATEUR (corrige et renvoie un JSON valide complet) ---\n"
                + fb
            )
        messages = [
            SystemMessage(content=SLOGAN_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        content = response.content if response and getattr(response, "content", None) else ""
        return content if isinstance(content, str) else str(content)

    @tool
    def draft_slogans(validation_feedback: str = "") -> str:
        """
        Produit un brouillon JSON avec la clé « slogan_options » (plusieurs slogans {text, rationale}).
        Premier appel : validation_feedback vide.
        Si validate_slogans échoue, rappeler avec le message d'erreur dans validation_feedback.
        """
        return _draft(validation_feedback)

    return draft_slogans


def make_validate_slogans_tool(
    *,
    target: int = SLOGAN_TARGET_COUNT,
    preferences: dict | None = None,
):

    avoid_tokens = _avoid_tokens(preferences)

    @traceable(name="tool.validate_slogans", tags=["branding", "tool", "slogan_validate"])
    def _validate(slogans_json: str) -> str:
        try:
            data = parse_llm_json_object(slogans_json)
        except Exception as e:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"JSON illisible ou invalide : {e}",
                    "validation_hints": "Renvoie un objet JSON avec la clé slogan_options (tableau).",
                },
                ensure_ascii=False,
                indent=2,
            )

        raw_opts = data.get("slogan_options")
        if not isinstance(raw_opts, list):
            return json.dumps(
                {
                    "ok": False,
                    "error": "Clé « slogan_options » manquante ou invalide.",
                    "validation_hints": "Le JSON doit contenir slogan_options : [ {\"text\":\"…\",\"rationale\":\"…\"}, … ]",
                },
                ensure_ascii=False,
                indent=2,
            )

        options = normalize_slogan_options(raw_opts)
        if len(options) < target:
            return json.dumps(
                {
                    "ok": False,
                    "error": (
                        f"Attendu {target} slogans exploitables, reçu {len(options)} "
                        "(texte non vide par entrée)."
                    ),
                    "validation_hints": f"Complète slogan_options avec exactement {target} slogans distincts.",
                },
                ensure_ascii=False,
                indent=2,
            )

        options = options[:target]

        for i, o in enumerate(options):
            text = str(o.get("text") or "").strip()
            if len(text) > SLOGAN_TEXT_MAX_LEN:
                return json.dumps(
                    {
                        "ok": False,
                        "error": f"Slogan {i + 1} : texte trop long (max {SLOGAN_TEXT_MAX_LEN} caractères).",
                        "validation_hints": "Raccourcis les accroches.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            if "\n" in text or "\r" in text:
                return json.dumps(
                    {
                        "ok": False,
                        "error": f"Slogan {i + 1} : pas de saut de ligne dans « text ».",
                        "validation_hints": "Une seule ligne par slogan.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            rat = str(o.get("rationale") or "").strip()
            if len(rat) < SLOGAN_RATIONALE_MIN_LEN:
                return json.dumps(
                    {
                        "ok": False,
                        "error": (
                            f"Slogan {i + 1} : « rationale » trop court "
                            f"(au moins {SLOGAN_RATIONALE_MIN_LEN} caractères)."
                        ),
                        "validation_hints": "Ajoute une courte phrase en français expliquant pourquoi le slogan convient.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )

            hit = _text_has_avoided_phrase(text, avoid_tokens)
            if hit:
                return json.dumps(
                    {
                        "ok": False,
                        "error": f"Slogan {i + 1} : contient une expression à éviter (« {hit} »).",
                        "validation_hints": "Reformule sans les termes listés dans mots_eviter.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )

        if not _slogans_pairwise_distinct(options):
            return json.dumps(
                {
                    "ok": False,
                    "error": "Les slogans ne sont pas assez distincts (doublons ou variantes trop proches).",
                    "validation_hints": "Propose des formulations clairement différentes.",
                },
                ensure_ascii=False,
                indent=2,
            )

        return json.dumps(
            {"ok": True, "slogan_options": options},
            ensure_ascii=False,
            indent=2,
        )

    @tool
    def validate_slogans(slogans_json: str) -> str:
        """
        Vérifie le JSON (sortie de draft_slogans) : nombre de slogans, texte, rationale,
        mots à éviter, unicité.
        """
        return _validate(slogans_json)

    return validate_slogans
