import asyncio
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import LLM_CONFIG, PALETTE_TARGET_COUNT
from llm.llm_factory import create_azure_openai_client
from prompts.branding.palette_prompt import (
    PALETTE_SYSTEM_PROMPT,
    build_palette_user_prompt,
)

logger = logging.getLogger("brandai.palette_agent")

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _first_brand_name_from_options(brand_identity: dict) -> str:
    opts = (brand_identity or {}).get("name_options") or []
    for o in opts:
        if isinstance(o, dict):
            nm = str(o.get("name") or "").strip()
            if nm:
                return nm
    return ""


def _normalize_hex(h: str) -> str | None:
    t = (h or "").strip()
    if not t:
        return None
    if t.startswith("#") and len(t) == 7 and _HEX_RE.match(t):
        return t.upper()
    if len(t) == 6 and re.match(r"^[0-9A-Fa-f]{6}$", t):
        return "#" + t.upper()
    return None


def _normalize_swatches(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("label") or "").strip()
        hx = _normalize_hex(str(item.get("hex") or item.get("color") or ""))
        if not name or not hx:
            continue
        role = str(item.get("role") or "accent").strip() or "accent"
        rationale = str(item.get("rationale") or item.get("description") or "").strip()
        out.append({"name": name, "hex": hx, "role": role, "rationale": rationale})
    return out


def _normalize_palette_options(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pname = str(item.get("palette_name") or item.get("name") or "").strip()
        sw = _normalize_swatches(item.get("swatches") or item.get("colors") or [])
        if not pname or len(sw) < 2:
            continue
        out.append({"palette_name": pname, "swatches": sw})
    return out


class PaletteAgent(BaseAgent):
    """Génère des palettes de couleurs à partir de l’idée clarifiée et du nom de marque (sans préférences utilisateur)."""

    def __init__(self):
        super().__init__(
            agent_name="palette_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=min(max(LLM_CONFIG.get("max_tokens") or 1200, 1800), 2400),
        )
        self._provider = LLM_CONFIG.get("provider", "groq")
        self._palette_max_tokens = min(max(LLM_CONFIG.get("max_tokens") or 1200, 1800), 2400)

    async def _invoke_palette_llm(self, system_prompt: str, user_prompt: str) -> str:
        if self._provider == "azure":
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            attempt = 0
            last_error = None
            while attempt < self.max_retries:
                try:
                    llm = create_azure_openai_client(
                        temperature=self.temperature,
                        max_tokens=self._palette_max_tokens,
                    )
                    response = await llm.ainvoke(messages)
                    content = response.content if response else ""
                    if not (content or "").strip():
                        raise RuntimeError("Empty response from Azure")
                    return content
                except Exception as e:
                    last_error = e
                    attempt += 1
                    await asyncio.sleep(2**attempt)
            raise RuntimeError(f"Azure palette LLM failed: {last_error}")

        return await self._call_llm(system_prompt, user_prompt)

    @traceable(name="palette_agent.run", tags=["branding", "palette_agent"])
    async def run(self, state: PipelineState) -> PipelineState:
        self._log_start(state)

        if not hasattr(state, "brand_identity") or state.brand_identity is None:
            state.brand_identity = {}

        brand_name = str(getattr(state, "brand_name_chosen", "") or "").strip()
        if not brand_name:
            brand_name = _first_brand_name_from_options(state.brand_identity)

        if not brand_name:
            msg = "Un nom de marque (choisi ou issu des propositions) est requis pour les palettes"
            state.brand_identity["palette_error"] = msg
            state.brand_identity["branding_status"] = "palette_failed"
            state.status = "palette_failed"
            state.errors.append(f"palette_agent: {msg}")
            self._log_error(msg)
            return state

        idea = state.clarified_idea or {}

        try:
            user_prompt = build_palette_user_prompt(
                idea,
                brand_name,
                target=PALETTE_TARGET_COUNT,
            )
            raw = await self._invoke_palette_llm(PALETTE_SYSTEM_PROMPT, user_prompt)
            data = self._parse_json(raw)
        except Exception as e:
            self._log_error(e)
            msg = str(e)
            state.errors.append(f"palette_agent: {msg}")
            state.brand_identity["palette_error"] = msg
            state.brand_identity["branding_status"] = "palette_failed"
            state.status = "palette_failed"
            return state

        options = _normalize_palette_options(data.get("palette_options") or [])
        if len(options) < PALETTE_TARGET_COUNT:
            msg = (
                f"Attendu {PALETTE_TARGET_COUNT} palettes distinctes, "
                f"reçu {len(options)} exploitable(s)"
            )
            state.brand_identity["palette_error"] = msg
            state.brand_identity["branding_status"] = "palette_failed"
            state.status = "palette_failed"
            self._log_error(msg)
            return state

        # Toujours exactement PALETTE_TARGET_COUNT (3) palettes côté produit
        if len(options) > PALETTE_TARGET_COUNT:
            logger.warning(
                "[palette_agent] %d palettes reçues — tronqué à %d",
                len(options),
                PALETTE_TARGET_COUNT,
            )
        options = options[:PALETTE_TARGET_COUNT]
        state.brand_identity["palette_options"] = options
        first = options[0]
        state.brand_identity["color_palette"] = {
            "palette_name": first.get("palette_name", ""),
            "swatches": first.get("swatches", []),
        }
        state.brand_identity.pop("palette_error", None)
        state.brand_identity["branding_status"] = "palette_generated"
        state.status = "palette_generated"
        self._log_success()
        logger.info(
            "[palette_agent] idea_id=%s brand=%s palettes=%s",
            state.idea_id,
            brand_name,
            len(options),
        )
        return state
