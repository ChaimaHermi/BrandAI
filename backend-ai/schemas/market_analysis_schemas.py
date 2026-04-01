# ══════════════════════════════════════════════════════════════
# schemas/market_analysis_schemas.py
# ══════════════════════════════════════════════════════════════

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, model_validator


# ── Section 1 : Overview ──────────────────────────────────────

class OverviewItem(BaseModel):
    niveau: str
    label:  str

class Overview(BaseModel):
    demande:     OverviewItem
    probleme:    OverviewItem
    concurrence: OverviewItem
    tendance:    OverviewItem


# ── Section 2 : Tendances ─────────────────────────────────────

class Tendances(BaseModel):
    direction:            str           = Field(..., description="RISING | STABLE | FALLING")
    signal_strength:      str           = Field(..., description="HIGH | MEDIUM | LOW")
    peak_period:          Optional[str] = None
    rising_queries:       list[str]     = Field(default_factory=list)
    hashtags:             list[str]     = Field(default_factory=list)
    hashtags_disponibles: bool          = False
    viral_score:          str           = Field(..., description="HIGH | MEDIUM | LOW | NONE")
    viral_signals:        list[str]     = Field(default_factory=list)
    sector_context:       str           = ""
    news_signals:         list[str]     = Field(default_factory=list)
    regulatory_barriers:  list[str]     = Field(default_factory=list)


# ── Section 3 : Market VOC ────────────────────────────────────

class VocDouleur(BaseModel):
    theme:      str
    recurrence: str  = Field(..., description="tres_elevee | elevee | moderee | faible")
    citation:   str
    source:     str

class Persona(BaseModel):
    segment:       str
    tranche_age:   str       = "non détecté"
    comportement:  str
    pain_points:   list[str] = Field(default_factory=list)
    motivations:   list[str] = Field(default_factory=list)
    signal_niveau: str

class Macro(BaseModel):
    population:     Optional[float] = None
    gdp_per_capita: Optional[float] = None
    internet_pct:   Optional[float] = None
    mobile_per100:  Optional[float] = None
    urban_pct:      Optional[float] = None
    youth_pct:      Optional[float] = None

class MarketVoc(BaseModel):
    demand_level:   str
    demand_summary: str
    top_voc:        list[VocDouleur] = Field(default_factory=list)
    personas:       list[Persona]    = Field(default_factory=list)
    macro:          Macro            = Field(default_factory=Macro)
    news_signals:   list[str]        = Field(default_factory=list)


# ── Section 4 : Competitor ────────────────────────────────────

class Competitor(BaseModel):
    nom:                  str
    type:                 str       = Field(..., description="digital | local | regional | international")
    website:              Optional[str] = None
    description:          Optional[str] = None
    source:               Optional[str] = None
    rating:               Optional[float] = None
    weaknesses:           List[str] = Field(default_factory=list)
    key_strengths:        List[str] = Field(default_factory=list)
    positioning:          Optional[str] = None

class CompetitorSection(BaseModel):
    top_competitors:     list[Competitor] = Field(default_factory=list)
    opportunite_niveau:  str              = Field(..., description="fenetre_ouverte | partielle | saturee")
    opportunite_summary: str


# ── Section 5 : SWOT ──────────────────────────────────────────

class SwotItem(BaseModel):
    point:  str
    source: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_swot_item(cls, values):
        if isinstance(values, str):
            return {"point": values, "source": "inference"}
        if isinstance(values, dict):
            if not values.get("point"):
                values["point"] = values.get("description") or values.get("label") or ""
            values.setdefault("source", values.get("source") or "inference")
        return values

class Swot(BaseModel):
    forces:       list[SwotItem] = Field(default_factory=list)
    faiblesses:   list[SwotItem] = Field(default_factory=list)
    opportunites: list[SwotItem] = Field(default_factory=list)
    menaces:      list[SwotItem] = Field(default_factory=list)


# ── Section 6 : Risques ───────────────────────────────────────

class Risque(BaseModel):
    type:        str = Field(..., description="reglementaire | macro | concurrentiel")
    cause:       str
    impact:      str
    probabilite: str
    mitigation:  Optional[str] = None

    @root_validator(pre=True)
    def _coerce_legacy_risque_fields(cls, values):
        # Compat legacy synthesis payloads.
        if not values.get("cause"):
            values["cause"] = values.get("description") or "Non precisé"
        if not values.get("impact"):
            values["impact"] = values.get("impact_attendu") or values.get("description") or "Non precisé"
        if not values.get("probabilite"):
            values["probabilite"] = values.get("niveau") or "moyen"
        if values.get("mitigation") is None:
            values["mitigation"] = values.get("mitigation")
        return values


# ── Section 7 : Recommandations ──────────────────────────────

class Recommandation(BaseModel):
    action:         str
    horizon:        Optional[str] = None
    impact_attendu: Optional[str] = None
    priorite:       Optional[int] = None
    source:         Optional[str] = None


# ── Meta ──────────────────────────────────────────────────────

class Meta(BaseModel):
    projet:         str
    secteur:        str
    geo:            str
    date_analyse:   str
    duree_secondes: float    = 0.0
    sources:        list[str] = Field(default_factory=list)
    appels_llm:     int       = 0
    appels_api:     int       = 0


# ── Rapport final ─────────────────────────────────────────────

class MarketReport(BaseModel):
    executive_summary: str = ""
    overview:        Overview
    tendances:       Tendances
    market_voc:      MarketVoc
    competitor:      CompetitorSection
    swot:            Swot
    risques:         list[Risque]        = Field(default_factory=list)
    recommandations: list[Recommandation] = Field(default_factory=list)
    meta:            Meta
    data_quality:    Dict[str, Any] = Field(default_factory=dict)