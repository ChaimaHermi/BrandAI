# ══════════════════════════════════════════════════════════════
# schemas/market_analysis_schemas.py
# ══════════════════════════════════════════════════════════════

from pydantic import BaseModel, Field
from typing import Optional


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
    faiblesse_principale: str
    weaknesses:           list[str] = Field(default_factory=list)
    key_strengths:        list[str] = Field(default_factory=list)
    positioning:          str       = ""

class CompetitorSection(BaseModel):
    top_competitors:     list[Competitor] = Field(default_factory=list)
    opportunite_niveau:  str              = Field(..., description="fenetre_ouverte | partielle | saturee")
    opportunite_summary: str


# ── Section 5 : SWOT ──────────────────────────────────────────

class SwotItem(BaseModel):
    point:  str
    source: str

class Swot(BaseModel):
    forces:       list[SwotItem] = Field(default_factory=list)
    faiblesses:   list[SwotItem] = Field(default_factory=list)
    opportunites: list[SwotItem] = Field(default_factory=list)
    menaces:      list[SwotItem] = Field(default_factory=list)


# ── Section 6 : Risques ───────────────────────────────────────

class Risque(BaseModel):
    type:        str  = Field(..., description="reglementaire | macro | concurrentiel")
    description: str
    source:      str


# ── Section 7 : Recommandations ──────────────────────────────

class Recommandation(BaseModel):
    priorite: int
    action:   str
    source:   str


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
    overview:        Overview
    tendances:       Tendances
    market_voc:      MarketVoc
    competitor:      CompetitorSection
    swot:            Swot
    risques:         list[Risque]        = Field(default_factory=list)
    recommandations: list[Recommandation] = Field(default_factory=list)
    meta:            Meta