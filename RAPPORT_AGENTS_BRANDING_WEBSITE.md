# Analyse Technique des Agents Brand AI
## Brand Kit (Branding) & Website Builder

---

## Table des matières

1. [Architecture générale du Brand Kit](#1-architecture-générale-du-brand-kit)
2. [Agent de Nommage — NameAgent](#2-agent-de-nommage--nameagent)
3. [Agent de Slogan — SloganAgent](#3-agent-de-slogan--sloganagent)
4. [Agent de Palette — PaletteAgent](#4-agent-de-palette--paletteagent)
5. [Agent de Logo — LogoAgent](#5-agent-de-logo--logoagent)
6. [Agent Website Builder — WebsiteBuilderOrchestrator](#6-agent-website-builder--websitebuilderorchestrator)
7. [Tableau récapitulatif des outils](#7-tableau-récapitulatif-des-outils)
8. [Schéma d'enchaînement global du Brand Kit](#8-schéma-denchaînement-global-du-brand-kit)

---

## 1. Architecture générale du Brand Kit

Le Brand Kit de Brand AI est composé de **quatre agents spécialisés** qui s'exécutent séquentiellement pour produire l'identité visuelle complète d'une startup. Chaque agent hérite de la classe abstraite `BaseAgent` et reçoit en entrée l'objet `PipelineState` qu'il enrichit avant de le passer au suivant.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PIPELINE BRANDING                          │
│                                                                     │
│  clarified_idea                                                     │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐    name_options     ┌───────────┐   slogan_options   │
│  │NameAgent │ ──────────────────► │SloganAgent│ ──────────────────►│
│  └──────────┘                     └───────────┘                    │
│                                                                     │
│  ┌──────────────┐  palette_options  ┌──────────┐  logo_concepts   │
│  │ PaletteAgent │ ────────────────► │ LogoAgent│ ───────────────► │
│  └──────────────┘                   └──────────┘    brand_identity│
└─────────────────────────────────────────────────────────────────────┘
```

**Classe de base commune :**

| Propriété | Valeur |
|-----------|--------|
| Fichier | `agents/base_agent.py` |
| Classe | `BaseAgent` |
| État partagé | `PipelineState` (dataclass) |
| Méthode principale | `async def run(state: PipelineState) -> PipelineState` |
| Traçabilité | LangSmith (projet `brand-ai`) |

**Configuration commune (branding_config.py) :**

| Paramètre | Valeur |
|-----------|--------|
| `LLM_CONFIG["provider"]` | `"azure"` |
| `LLM_CONFIG["model"]` | `"gpt-4o"` |
| `LLM_CONFIG["temperature"]` | `0.65` |
| `LLM_CONFIG["max_tokens"]` | `4000` |

---

## 2. Agent de Nommage — NameAgent

### 2.1 Description générale

Le `NameAgent` est responsable de la génération de **noms de marque disponibles** pour la startup. Il utilise une architecture **ReAct (Reason + Act)** via LangGraph qui boucle entre génération LLM et vérification de disponibilité réelle via l'API Brandfetch, jusqu'à obtenir le nombre cible de noms disponibles.

**Fichier source :** `agents/branding/name_agent.py`

### 2.2 Configuration technique

| Paramètre | Valeur |
|-----------|--------|
| Modèle LLM | `gpt-4o` (Azure OpenAI) |
| Température | `0.65` |
| Max tokens | `4000` |
| Fournisseur | Azure |
| Limite de récursion | `55` itérations |
| Nombre cible de noms | `3` noms disponibles |
| Architecture | LangGraph `create_react_agent` |
| Mémoire court terme | SQLite (`data/memory/short_term/naming_short_term.db`) |

### 2.3 Outils utilisés

L'agent dispose de **2 outils LangChain** définis dans `tools/branding/name_tools.py` :

#### Outil 1 — `generate_names`
- **Rôle :** Demande au LLM de brainstormer des noms de marque créatifs
- **Entrée :** Chaîne de noms déjà générés à exclure (séparés par des virgules)
- **Logique interne :**
  - Charge la mémoire court terme SQLite des noms déjà vérifiés comme existants
  - Fusionne avec la liste d'exclusion dynamique
  - Construit le prompt via `build_name_user_prompt(idea, excluded_names)`
  - Appelle `llm.invoke(prompt)` → renvoie JSON avec `name_options`
- **Sortie :** JSON `{"name_options": [{"name": "...", "description": "..."}]}`

#### Outil 2 — `validate_names`
- **Rôle :** Vérifier la disponibilité réelle de chaque nom via Brandfetch API
- **Entrée :** JSON des noms à vérifier
- **Logique interne :**
  - Pour chaque nom : appel HTTP GET `https://api.brandfetch.io/v2/search/{nom_normalisé}`
  - Normalisation du nom : suppression des caractères non alphanumériques
  - Comparaison avec les marques retournées (matching exact normalisé)
  - Mémorise les noms existants dans SQLite pour ne pas les reproposer
- **Sortie :** JSON `[{"name": "...", "availability": "not_exists"|"exists", "matched_name": ...}]`

### 2.4 Flux de traitement détaillé

```
run(state: PipelineState)
│
├─ 1. Validation des champs obligatoires
│      [sector, target_users, problem, solution_description, country]
│      → Si manquants : retour avec status = "name_failed"
│
├─ 2. Construction du contexte idée (idea_context dict)
│      + attachement des préférences de nommage (naming_preferences)
│
├─ 3. Boucle de tentatives (max_retries pour gestion quota Azure)
│      │
│      └─ Création client Azure OpenAI (gpt-4o, temp=0.65)
│         │
│         └─ _run_react_name_agent(llm, idea_context, target=3, recursion_limit=55)
│                │
│                ├─ Création des outils : generate_names + validate_names
│                ├─ Initialisation du graph LangGraph ReAct
│                └─ Boucle ReAct (max 55 itérations) :
│                       │
│                       ├─ [THOUGHT] LLM réfléchit : combien de noms available ?
│                       ├─ [ACTION] generate_names(excluded="nom1,nom2,...")
│                       ├─ [OBSERVATION] LLM reçoit les noms générés (JSON)
│                       ├─ [ACTION] validate_names(names_json="{...}")
│                       ├─ [OBSERVATION] LLM reçoit les disponibilités
│                       └─ Si < 3 "not_exists" → recommencer, sinon STOP
│
├─ 4. Extraction des noms disponibles depuis les ToolMessages
│      (lecture de l'historique des messages, filtre availability="not_exists")
│
└─ 5. Écriture dans state.brand_identity["name_options"]
       status = "name_generated"
```

### 2.5 Gestion des erreurs et quota

- **TPD (Tokens Per Day) épuisé :** Erreur levée immédiatement avec message explicite
- **Erreur 429 / rate limit :** Rotation vers une autre clé API (llm_rotator.rotate())
- **Résultat vide :** Status `name_failed` avec message d'erreur détaillé

### 2.6 Format de sortie

```json
{
  "name_options": [
    {
      "name": "APIHub",
      "description": "Plateforme unifiée d'intégration API",
      "availability": "not_exists",
      "matched_name": null,
      "top_choice": true
    },
    {
      "name": "IntegrateX",
      "description": "Solution d'intégration nouvelle génération",
      "availability": "not_exists",
      "matched_name": null,
      "top_choice": true
    },
    {
      "name": "UnifyAPI",
      "description": "Unifie toutes tes intégrations en une seule API",
      "availability": "not_exists",
      "matched_name": null,
      "top_choice": true
    }
  ],
  "branding_status": "name_generated"
}
```

### 2.7 Diagramme de séquence — NameAgent

```
┌──────────┐   ┌──────────────┐   ┌───────────────────┐   ┌───────────────┐   ┌──────────────────┐
│  Client  │   │  FastAPI     │   │    NameAgent       │   │  Azure gpt-4o │   │  Brandfetch API  │
│ Frontend │   │  (backend-ai)│   │ (LangGraph ReAct)  │   │  (LLM)        │   │  (HTTP REST)     │
└────┬─────┘   └──────┬───────┘   └────────┬──────────┘   └───────┬───────┘   └────────┬─────────┘
     │                │                    │                       │                    │
     │ POST /branding/name                 │                       │                    │
     │ {clarified_idea}                    │                       │                    │
     │───────────────►│                    │                       │                    │
     │                │ run(state)         │                       │                    │
     │                │───────────────────►│                       │                    │
     │                │                    │                       │                    │
     │                │                    │ [Init ReAct Graph]    │                    │
     │                │                    │ create_react_agent()  │                    │
     │                │                    │                       │                    │
     │                │           ╔════════╪═══════════╗           │                    │
     │                │           ║  BOUCLE ReAct       ║           │                    │
     │                │           ╠════════╪═══════════╣           │                    │
     │                │           ║        │ [THOUGHT]  ║           │                    │
     │                │           ║        │ ainvoke()  │─────────►│                    │
     │                │           ║        │            │◄─────────│                    │
     │                │           ║        │ tool_call: generate_names(excluded="")     │
     │                │           ║        │─────────────────────►│                    │
     │                │           ║        │ name_options JSON    │                    │
     │                │           ║        │◄─────────────────────│                    │
     │                │           ║        │ [OBSERVATION reçue]   │                    │
     │                │           ║        │                       │                    │
     │                │           ║        │ tool_call: validate_names(names_json)      │
     │                │           ║        │──────────────────────────────────────────►│
     │                │           ║        │                       │  GET /v2/search/   │
     │                │           ║        │                       │  {nom_normalisé}   │
     │                │           ║        │                       │◄──────────────────│
     │                │           ║        │  [{name, availability}]                   │
     │                │           ║        │◄──────────────────────────────────────────│
     │                │           ║        │                       │                    │
     │                │           ║        │ [Si < 3 not_exists → recommencer]         │
     │                │           ╚════════╪═══════════╝           │                    │
     │                │                    │                       │                    │
     │                │                    │ Extraction available  │                    │
     │                │                    │ depuis ToolMessages   │                    │
     │                │                    │                       │                    │
     │                │  state (name_options, status="name_generated")                 │
     │                │◄───────────────────│                       │                    │
     │  {name_options: [...]}              │                       │                    │
     │◄───────────────│                    │                       │                    │
```

---

## 3. Agent de Slogan — SloganAgent

### 3.1 Description générale

Le `SloganAgent` génère des **slogans/taglines** percutants pour la marque. Contrairement au NameAgent, il utilise une architecture **directe (appel LLM unique)** sans boucle ReAct, car les slogans ne nécessitent pas de validation externe — une validation minimale locale suffit.

**Fichier source :** `agents/branding/slogan_agent.py`

### 3.2 Configuration technique

| Paramètre | Valeur |
|-----------|--------|
| Modèle LLM | `gpt-4o` (Azure OpenAI) |
| Température | `0.65` |
| Max tokens | `min(4000, 1600) = 1600` |
| Fournisseur | Azure |
| Architecture | **Appel LLM direct** (sans ReAct) |
| Nombre cible | `3` slogans |
| Validation | Locale (validate_minimal_slogans) |

### 3.3 Prérequis

L'agent requiert que **`brand_name_chosen`** soit présent dans le state (nom de marque choisi par l'utilisateur parmi les propositions du NameAgent).

### 3.4 Outils utilisés

Le SloganAgent n'utilise pas d'outils LangChain. Il effectue un seul appel LLM avec :

- **Prompt système :** `SLOGAN_SYSTEM_PROMPT` (défini dans `prompts/branding/slogan_prompt.py`)
- **Prompt utilisateur :** `build_slogan_user_prompt(idea, brand_name, prefs, target=3)`
  - Inclut : secteur, utilisateurs cibles, problème, solution, nom de marque, préférences de ton
- **Validation :** `validate_minimal_slogans(raw, target=3)` (dans `shared/branding/validators.py`)
  - Parse le JSON retourné par le LLM
  - Vérifie qu'au moins 3 slogans sont présents
  - Retourne une liste normalisée

### 3.5 Flux de traitement détaillé

```
run(state: PipelineState)
│
├─ 1. Vérification : brand_name_chosen présent ?
│      → Sinon : status = "slogan_failed"
│
├─ 2. Extraction contexte idée (idea, prefs)
│
├─ 3. _generate_raw_slogans(idea, brand_name, prefs)
│      │
│      ├─ Création client Azure OpenAI (gpt-4o, temp=0.65, max_tokens=1600)
│      ├─ [SystemMessage] SLOGAN_SYSTEM_PROMPT
│      ├─ [HumanMessage] build_slogan_user_prompt(...)
│      └─ llm.ainvoke(messages) → raw string (JSON slogans)
│
├─ 4. validate_minimal_slogans(raw, target=3)
│      → Parse JSON → liste de slogans normalisés
│
└─ 5. Écriture dans state.brand_identity
       ["slogan_options"] = options
       ["chosen_brand_name"] = brand_name
       status = "slogan_generated"
```

### 3.6 Format de sortie

```json
{
  "slogan_options": [
    {
      "slogan": "One API, Infinite Possibilities",
      "vibe": "Inspirant et professionnel",
      "language": "en"
    },
    {
      "slogan": "Connectez tout, créez l'essentiel",
      "vibe": "Moderne et accessible",
      "language": "fr"
    },
    {
      "slogan": "L'intégration, réinventée",
      "vibe": "Minimaliste et percutant",
      "language": "fr"
    }
  ],
  "chosen_brand_name": "APIHub",
  "branding_status": "slogan_generated"
}
```

### 3.7 Diagramme de séquence — SloganAgent

```
┌──────────┐   ┌──────────────┐   ┌──────────────────┐   ┌───────────────┐
│  Client  │   │  FastAPI     │   │   SloganAgent     │   │  Azure gpt-4o │
│ Frontend │   │  (backend-ai)│   │ (Appel LLM direct)│   │  (LLM)        │
└────┬─────┘   └──────┬───────┘   └────────┬─────────┘   └───────┬───────┘
     │                │                    │                      │
     │ POST /branding/slogan               │                      │
     │ {brand_name_chosen, clarified_idea} │                      │
     │───────────────►│                    │                      │
     │                │ run(state)         │                      │
     │                │───────────────────►│                      │
     │                │                    │                      │
     │                │                    │ Vérification         │
     │                │                    │ brand_name_chosen    │
     │                │                    │                      │
     │                │                    │ build_slogan_prompt() │
     │                │                    │                      │
     │                │                    │ [SystemMessage]      │
     │                │                    │ [HumanMessage]       │
     │                │                    │─────────────────────►│
     │                │                    │                      │ Génération LLM
     │                │                    │                      │ (température=0.65)
     │                │                    │   raw JSON slogans   │
     │                │                    │◄─────────────────────│
     │                │                    │                      │
     │                │                    │ validate_minimal_slogans(raw)
     │                │                    │ (parsing + normalisation locale)
     │                │                    │                      │
     │                │ state (slogan_options, status="slogan_generated")
     │                │◄───────────────────│                      │
     │  {slogan_options: [...]}            │                      │
     │◄───────────────│                    │                      │
```

---

## 4. Agent de Palette — PaletteAgent

### 4.1 Description générale

Le `PaletteAgent` génère des **palettes de couleurs** cohérentes avec l'identité de la marque et son secteur. Il suit la même architecture directe que le SloganAgent (appel LLM unique + validation locale).

**Fichier source :** `agents/branding/palette_agent.py`

### 4.2 Configuration technique

| Paramètre | Valeur |
|-----------|--------|
| Modèle LLM | `gpt-4o` (Azure OpenAI) |
| Température | `0.65` |
| Max tokens | `4000` |
| Fournisseur | Azure |
| Architecture | **Appel LLM direct** (sans ReAct) |
| Nombre cible | `3` palettes |
| Validation | Locale (`validate_minimal_palettes`) |

### 4.3 Logique de récupération du nom de marque

L'agent tente de récupérer le nom de marque de deux façons :
1. **`state.brand_name_chosen`** : nom explicitement sélectionné par l'utilisateur
2. **Fallback :** premier nom de `state.brand_identity["name_options"]` (si brand_name_chosen absent)

### 4.4 Flux de traitement détaillé

```
run(state: PipelineState)
│
├─ 1. Récupération brand_name
│      ├─ state.brand_name_chosen → priorité
│      └─ Fallback : premier nom de name_options
│         → Si aucun : status = "palette_failed"
│
├─ 2. Extraction contexte idée (secteur, pays, cible…)
│
├─ 3. _generate_raw_palettes(idea, brand_name)
│      │
│      ├─ Création client Azure OpenAI (gpt-4o, temp=0.65, max_tokens=4000)
│      ├─ [SystemMessage] PALETTE_SYSTEM_PROMPT
│      ├─ [HumanMessage] build_palette_user_prompt(idea, brand_name, target=3)
│      └─ llm.ainvoke(messages) → raw string (JSON palettes)
│
├─ 4. validate_minimal_palettes(raw, target=3)
│      → Parse JSON → liste de palettes normalisées (avec swatches hex)
│
└─ 5. Écriture dans state.brand_identity
       ["palette_options"] = options (toutes les palettes)
       ["color_palette"]   = options[0] (palette principale retenue)
       status = "palette_generated"
```

### 4.5 Format de sortie

```json
{
  "palette_options": [
    {
      "palette_name": "Ocean Tech",
      "palette_description": "Couleurs fraîches et modernes évoquant la fiabilité",
      "swatches": [
        {"name": "Primary",   "hex": "#0066FF", "usage": "CTA, accents"},
        {"name": "Dark",      "hex": "#001166", "usage": "Fonds sombres, textes"},
        {"name": "Light",     "hex": "#E8F0FF", "usage": "Arrière-plans"},
        {"name": "Neutral",   "hex": "#FFFFFF", "usage": "Fond principal"},
        {"name": "Accent",    "hex": "#FF6600", "usage": "Mises en avant"}
      ]
    }
  ],
  "color_palette": { "palette_name": "Ocean Tech", "swatches": [...] },
  "branding_status": "palette_generated"
}
```

### 4.6 Diagramme de séquence — PaletteAgent

```
┌──────────┐   ┌──────────────┐   ┌──────────────────┐   ┌───────────────┐
│  Client  │   │  FastAPI     │   │   PaletteAgent    │   │  Azure gpt-4o │
│ Frontend │   │  (backend-ai)│   │ (Appel LLM direct)│   │  (LLM)        │
└────┬─────┘   └──────┬───────┘   └────────┬─────────┘   └───────┬───────┘
     │                │                    │                      │
     │ POST /branding/palette              │                      │
     │ {brand_name_chosen, clarified_idea} │                      │
     │───────────────►│                    │                      │
     │                │ run(state)         │                      │
     │                │───────────────────►│                      │
     │                │                    │                      │
     │                │                    │ Résolution brand_name│
     │                │                    │ (chosen ou fallback) │
     │                │                    │                      │
     │                │                    │ build_palette_prompt()
     │                │                    │                      │
     │                │                    │ [SystemMessage]      │
     │                │                    │ [HumanMessage]       │
     │                │                    │─────────────────────►│
     │                │                    │                      │ Génération LLM
     │                │                    │                      │ (température=0.65)
     │                │                    │   raw JSON palettes  │
     │                │                    │◄─────────────────────│
     │                │                    │                      │
     │                │                    │ validate_minimal_palettes(raw)
     │                │                    │ Extraction palette principale
     │                │                    │                      │
     │                │ state (palette_options, color_palette, status="palette_generated")
     │                │◄───────────────────│                      │
     │  {palette_options: [...]}           │                      │
     │◄───────────────│                    │                      │
```

---

## 5. Agent de Logo — LogoAgent

### 5.1 Description générale

Le `LogoAgent` est l'agent le plus complexe du Brand Kit. Il génère un **logo professionnel** en suivant un pipeline en plusieurs étapes : rédaction d'un prompt image par le LLM (gpt-4.1), génération de l'image via HuggingFace, suppression du fond, et vérification d'originalité via Google Lens (SerpAPI).

**Fichier source :** `agents/branding/logo_agent.py`

### 5.2 Configuration technique

| Paramètre | Valeur |
|-----------|--------|
| Modèle LLM | `gpt-4.1` (Azure OpenAI — déploiement logo) |
| Température | `0.4` |
| Max tokens | `min(900, 1200) = 900` |
| Fournisseur LLM | Azure |
| Générateur d'image | HuggingFace (`Qwen/Qwen-Image`) |
| Fallback image | Désactivé (`pollinations_fallback=False`) |
| Vérification originalité | Activée (SerpAPI Google Lens) |
| Max retries originalité | `2` |
| Max images similaires tolérées | `2` |
| Suppression fond | `rembg` (ou PIL threshold=245 en fallback) |

### 5.3 Outils utilisés

L'agent utilise **2 outils** définis dans `tools/branding/logo_tools.py` :

#### Outil 1 — `draft_logo_prompt`
- **Rôle :** Demande au LLM de rédiger un prompt image JSON pour la génération text-to-image
- **Entrée :** `validation_feedback` (string — vide au premier appel, erreur si rejet)
- **Logique :**
  - Construit `build_logo_user_message(idea, brand_name, slogan_hint, palette_hint)`
  - Si feedback non vide → ajoute "--- VALIDATOR FEEDBACK ---" au prompt
  - Appelle `llm.invoke([SystemMessage, HumanMessage])` → JSON
- **Sortie :** `{"image_prompt": "...", "negative_prompt": "..."}`

#### Outil 2 — `render_logo_image`
- **Rôle :** Génère l'image du logo via HuggingFace Inference API
- **Entrée :** `image_prompt` (str), `negative_prompt` (str)
- **Logique :**
  - Vérifie que `LOGO_IMAGE_PROVIDER != "none"`
  - Appelle `fetch_logo_image_hf_with_pollinations_fallback(ip, np, model="Qwen/Qwen-Image", pollinations_fallback=False)`
  - Stocke les bytes dans le `holder` dict partagé
- **Sortie :** JSON `{"ok": true, "byte_count": ..., "source": "huggingface", "mime": "image/png"}`

**Outil annexe — `validate_logo_prompt`** (utilisé dans le mode ReAct historique) :
- Valide le JSON produit par `draft_logo_prompt`
- Contraintes vérifiées :
  - Longueur `image_prompt` : entre 32 et 460 caractères
  - `negative_prompt` : max 220 caractères
  - Le nom de la marque doit apparaître dans `image_prompt`
  - Interdit : codes couleur hex (`#RRGGBB`), mots `badge/label/plate/sticker`

### 5.4 Post-traitement de l'image

```
image_bytes (PNG/JPEG)
       │
       ▼
_remove_light_background_to_transparent(image_bytes)
       │
       ├─ Tentative 1 : rembg.remove(image_bytes)
       │       → Segmentation IA (plus précise)
       │
       └─ Fallback : PIL RGBA threshold
               → Pixels avec min(R,G,B) ≥ 245 → alpha=0
               → Transition douce (feather=25px)
               → Sauvegarde en PNG avec canal alpha
```

### 5.5 Vérification d'originalité

```
concept["image_base64"] disponible
       │
       ▼
verifier_originalite_logo_bytes(raw_bytes, max_similar=2)
       │  (tools/branding/logo_originality_checker.py)
       │
       ├─ Upload image → URL temporaire
       ├─ Appel SerpAPI : Google Lens reverse image search
       ├─ Compte les correspondances visuelles trouvées
       │
       ├─ is_original = True si nb_similaires ≤ 2
       │       → On garde le concept
       │
       └─ is_original = False (max 2 retries)
               → Génération d'un nouveau concept
               → Feedback : "ORIGINALITY ISSUE — trop similaire à..."
               → Demande de changer complètement l'icône et la composition
```

### 5.6 Flux de traitement détaillé

```
run(state: PipelineState)
│
├─ 1. Vérification : brand_name_chosen présent ?
│      → Sinon : status = "logo_failed"
│
├─ 2. Extraction :
│      idea, palette_hint (couleurs choisies)
│      previous_prompt (si régénération) + user_remarks
│
├─ 3. Construction du feedback de régénération (si applicable)
│      "REGENERATION REQUEST — the user did not like the previous logo..."
│
├─ 4. _make_llm_for_logo() → client Azure gpt-4.1
│
├─ 5. _generate_logo_concept(llm, idea, brand_name, palette_hint)
│      │
│      ├─ _draft_logo_prompt_direct(llm, ...)
│      │      ├─ build_logo_user_message_with_name(idea, brand_name, palette_hint)
│      │      ├─ llm.invoke([SystemMessage(LOGO_IMAGE_PROMPT_SYSTEM_WITH_NAME), HumanMessage])
│      │      └─ _parse_logo_prompt_json(raw, brand_name) → (image_prompt, negative_prompt)
│      │
│      ├─ _maybe_fetch_image(image_prompt, negative_prompt)
│      │      └─ fetch_logo_image_hf_with_pollinations_fallback(ip, np, model="Qwen/Qwen-Image")
│      │             → image_bytes, mime, source
│      │
│      ├─ base64.encode(image_bytes) → b64
│      └─ _remove_light_background_to_transparent(image_bytes) → transparent_b64
│
├─ 6. Vérification d'originalité (si LOGO_ORIGINALITY_CHECK_ENABLED=True)
│      └─ Boucle max 2 retries si logo trop similaire
│
├─ 7. Promotion version transparente comme image principale
│      (concept["image_base64"] = transparent_b64)
│
└─ 8. Écriture dans state.brand_identity
       ["logo_concepts"] = [concept]
       status = "logo_generated"
```

### 5.7 Format de sortie

```json
{
  "logo_concepts": [
    {
      "title": "Generated mark",
      "image_prompt": "Minimalist wordmark logo for 'APIHub'...",
      "negative_prompt": "blurry, low quality, badge, frame...",
      "image_base64": "iVBORw0KGgoAAAANS...",
      "image_mime": "image/png",
      "image_base64_transparent": "iVBORw0KGgoAAAANS...",
      "image_mime_transparent": "image/png",
      "image_provider": "huggingface",
      "image_model": "Qwen/Qwen-Image",
      "image_attribution": "Image générée avec Hugging Face Inference — modèle Qwen/Qwen-Image."
    }
  ],
  "branding_status": "logo_generated"
}
```

### 5.8 Diagramme de séquence — LogoAgent

```
┌──────────┐  ┌──────────┐  ┌───────────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────────┐
│  Client  │  │  FastAPI │  │   LogoAgent   │  │ Azure      │  │ HuggingFace │  │  SerpAPI     │
│ Frontend │  │(backend) │  │               │  │ gpt-4.1    │  │ Inference   │  │ Google Lens  │
└────┬─────┘  └────┬─────┘  └───────┬───────┘  └─────┬──────┘  └──────┬──────┘  └──────┬───────┘
     │              │               │                 │                │                │
     │ POST /logo   │               │                 │                │                │
     │ {brand_name} │               │                 │                │                │
     │─────────────►│               │                 │                │                │
     │              │ run(state)    │                 │                │                │
     │              │──────────────►│                 │                │                │
     │              │               │                 │                │                │
     │              │               │ [Phase 1] Draft prompt          │                │
     │              │               │ LOGO_IMAGE_PROMPT_SYSTEM_WITH_NAME               │
     │              │               │─────────────────────────────────►                │
     │              │               │ {"image_prompt": "...",          │                │
     │              │               │  "negative_prompt": "..."}       │                │
     │              │               │◄─────────────────────────────────                │
     │              │               │                 │                │                │
     │              │               │ [Phase 2] Génération image       │                │
     │              │               │─────────────────────────────────────────────────►│
     │              │               │                 │  POST /models/Qwen/Qwen-Image   │
     │              │               │                 │  {inputs: image_prompt}         │
     │              │               │                 │◄────────────────────────────────│
     │              │               │   image_bytes (PNG)             │                │
     │              │               │◄─────────────────────────────────────────────────│
     │              │               │                 │                │                │
     │              │               │ [Phase 3] Suppression fond                        │
     │              │               │ rembg.remove(image_bytes) → transparent_bytes    │
     │              │               │                 │                │                │
     │              │               │ [Phase 4] Vérification originalité               │
     │              │               │─────────────────────────────────────────────────►│
     │              │               │                 │  Google Lens reverse search     │
     │              │               │                 │  {image_url}                   │
     │              │               │   {matches: [...], is_original: true}            │
     │              │               │◄─────────────────────────────────────────────────│
     │              │               │                 │                │                │
     │              │ state (logo_concepts, status="logo_generated")  │                │
     │              │◄──────────────│                 │                │                │
     │  {logo_b64, prompt_used}     │                 │                │                │
     │◄─────────────│               │                 │                │                │
```

---

## 6. Agent Website Builder — WebsiteBuilderOrchestrator

### 6.1 Description générale

Le `WebsiteBuilderOrchestrator` est l'agent le plus élaboré du système. Il orchestre la **création complète d'un site vitrine HTML** à partir du brand kit et de l'idée de startup, en passant par plusieurs phases : conception créative, génération HTML/Tailwind/JS, validation qualité, révision, et déploiement sur Vercel. Il expose ses fonctions via des **routes SSE (Server-Sent Events)** pour un retour en temps réel.

**Fichier source :** `agents/website_builder/orchestrator.py`

### 6.2 Configuration technique

| Paramètre | Valeur |
|-----------|--------|
| Modèle LLM | `openai/gpt-oss-120b` (NVIDIA NIM) |
| Fournisseur LLM | NVIDIA NIM |
| Architecture | Orchestrateur multi-phases (non-ReAct) |
| Streaming | SSE (Server-Sent Events) |
| Traçabilité | LangSmith (tags: `website_builder`, `stream`) |
| Déploiement | Vercel API |

### 6.3 Outils utilisés (tools/website_builder/)

| Outil | Fichier | Rôle |
|-------|---------|------|
| `WebsiteContextTool` | `context_tool.py` | Récupère le brand kit + l'idée depuis backend-api |
| `generate_website_architecture` | `architecture_tool.py` | Phase 2A : génère la structure (sections, animations, navigation) |
| `generate_website_content` | `content_tool.py` | Phase 2B : génère le contenu textuel de chaque section |
| `build_website_html` | `coder_tool.py` | Phase 3 : génère le code HTML/Tailwind/JS complet |
| `refine_website_description` | `refinement_tool.py` | Phase 2.5 : affine la description selon les retours utilisateur |
| `revise_website_html` | `revision_tool.py` | Phase 4 : applique une modification chirurgicale sur le HTML |
| `validate_brand_identity` | `validator_tool.py` | QA : vérifie présence nom de marque et slogan dans le HTML |
| `validate_html_output` | `validator_tool.py` | QA : vérifie navigation, images, responsive |
| `sanitize_navigation_html` | `validator_tool.py` | Nettoie les liens de navigation invalides |
| `deploy_html_to_vercel` | `vercel_deploy.py` | Déploie le HTML sur Vercel |
| `delete_vercel_deployment` | `vercel_deploy.py` | Supprime un déploiement Vercel |
| `patch_website_project` | `website_project_persistence.py` | Persiste l'état dans backend-api |
| `append_website_message` | `website_project_persistence.py` | Historique de conversation du projet |
| `StepEmitter` | `step_streamer.py` | Émetteur d'événements SSE en temps réel |

### 6.4 Les 4 phases de génération

#### Phase 1 — Chargement du contexte (`fetch_context`)
```
WebsiteContextTool.fetch(idea_id, access_token)
    → Appel HTTP vers backend-api :
      - GET /ideas/{idea_id} → clarified_idea
      - GET /brand-identity/{idea_id} → name, slogan, palette, logo
    → Retourne WebsiteContext :
      {brand_name, slogan, color_palette, logo_url, language, sector, ...}
```

#### Phase 2A — Architecture (`generate_website_architecture`)
```
LLM (NVIDIA gpt-oss-120b) génère :
{
  "sections": [
    {"id": "hero", "type": "hero", "purpose": "...", "has_cta": true},
    {"id": "features", "type": "features", "purpose": "..."},
    {"id": "pricing", "type": "pricing", "purpose": "..."},
    {"id": "contact", "type": "contact", "purpose": "..."}
  ],
  "nav_links": ["#features", "#pricing", "#contact"],
  "animations": ["fade-in-up", "slide-in-left"],
  "visual_style": "modern-minimal",
  "tone": "professionnel et accessible",
  "language": "fr"
}
```

#### Phase 2B — Contenu (`generate_website_content`)
```
LLM génère le contenu textuel pour chaque section :
{
  "sections": {
    "hero": {
      "headline": "Une API pour les unifier toutes",
      "subheadline": "Simplifiez vos intégrations avec APIHub",
      "cta_text": "Commencer gratuitement"
    },
    "features": { ... },
    "contact": { ... }
  },
  "meta": {
    "title": "APIHub — Intégrations API unifiées",
    "description": "..."
  }
}
```

#### Phase 3 — Génération HTML (`build_website_html`)
```
LLM génère le HTML complet (Tailwind CSS + animations JS) :
- Fichier HTML unique, auto-suffisant
- Tailwind CSS (CDN)
- Couleurs de la palette intégrées
- Logo présent (img ou SVG inline)
- Nom de marque + slogan obligatoires
- Navigation par ancres #id (aucun href="#" nu)
- Images : src http/https/data, alt, fallback
- Responsive : meta viewport, breakpoints sm/md/lg, nav mobile
```

#### Phase 4 — Validation QA (`_ensure_valid_html`)
```
validate_brand_identity(html, brand_name, slogan)
    → Vérifie présence verbatim du nom et du slogan
    → RuntimeError si absent

validate_html_output(html)
    → Vérifie navigation (ancres #id valides, pas de href="#" nu)
    → Vérifie images (src, alt, fallback)
    → Vérifie responsive (meta viewport, breakpoints)
    → Retourne stats {sections, images, links, ...}

Si erreur QA → auto-correction :
    revise_website_html(ctx, html, auto_fix_instruction, invoke_llm)
    → LLM corrige uniquement les problèmes QA
    → Revalidation immédiate
```

### 6.5 Flux de traitement détaillé — Génération de site

```
stream_generate_website(idea_id, token, description, emitter)
│
├─ [SSE: "context"] Phase 1 : Chargement du contexte brand kit
│      WebsiteContextTool.fetch(idea_id, token)
│      → Émet : {brand_name, slogan, palette, language}
│
├─ [SSE: "design"] Phase 2 : Si description absente → génération à la volée
│      _generate_full_description(ctx)
│      ├─ generate_website_architecture(ctx, invoke_llm, parse_json)
│      └─ generate_website_content(ctx, architecture, invoke_llm, parse_json)
│
├─ [SSE: "build"] Phase 3 : Génération HTML complet
│      build_website_html(ctx, architecture, content, invoke_llm)
│      → HTML Tailwind + JS animations
│
├─ [SSE: "qa"] Phase 4 : Validation qualité
│      _ensure_valid_html(ctx, html, phase="generation")
│      ├─ sanitize_navigation_html(html)
│      ├─ validate_brand_identity(html, brand_name, slogan)
│      ├─ validate_html_output(html) → stats
│      └─ Si erreur → revise_website_html() + revalidation
│
├─ [SSE: "persist"] Sauvegarde
│      patch_website_project(idea_id, {status: "generated", current_html: html, version: 1})
│      append_website_message(idea_id, {type: "generation_result", meta: stats})
│
└─ [SSE: "result"] Réponse finale
       {context, description, html, html_stats}
```

### 6.6 Routes SSE disponibles

| Route | Phase | Description |
|-------|-------|-------------|
| `GET /website/context` | — | Récupère le contexte brand kit (non streaming) |
| `POST /website/description/stream` | Phase 2 | Génère le concept créatif (streaming) |
| `POST /website/description/refine/stream` | Phase 2.5 | Affine le concept selon retours (streaming) |
| `POST /website/description/approve` | — | Valide le concept pour passer à la génération |
| `POST /website/generate/stream` | Phase 3+4 | Génère le HTML complet + QA (streaming) |
| `POST /website/revise/stream` | Phase 4 | Révise le HTML selon instruction (streaming) |
| `POST /website/save` | — | Sauvegarde HTML modifié manuellement |
| `POST /website/deploy` | Déploiement | Déploie sur Vercel |
| `POST /website/deploy/delete` | — | Supprime un déploiement Vercel |

### 6.7 Format des événements SSE

```
event: step
data: {"step_id": "build", "message": "Phase 3 - Écriture du HTML...", "status": "loading"}

event: step
data: {"step_id": "build", "message": "HTML généré.", "status": "done", "meta": {...}}

event: step
data: {"step_id": "qa", "message": "Validation qualité...", "status": "loading"}

event: step
data: {"step_id": "qa", "message": "Site validé.", "status": "done",
       "meta": {"sections": 4, "images": 3, "links": 8}}

event: result
data: {
  "context": {"brand_name": "APIHub", "slogan": "...", ...},
  "description": {"sections": [...], "animations": [...]},
  "html": "<!DOCTYPE html>...",
  "html_stats": {"sections": 4, "images": 3}
}
```

### 6.8 Déploiement Vercel

```
deploy_website(idea_id, token, html)
│
├─ validate_html_document(html) → vérification structurelle
│
├─ deploy_html_to_vercel(html, idea_id, brand_name)
│      │  (tools/website_builder/vercel_deploy.py)
│      ├─ Appel API Vercel (POST /v13/deployments)
│      ├─ Payload : {name: brand_name, files: [{path: "index.html", data: html}]}
│      ├─ En-tête : Authorization: Bearer {VERCEL_TOKEN}
│      └─ Retourne : {deployment_id, full_url, project_name, state, elapsed_seconds}
│
├─ patch_website_project(idea_id, {status: "deployed", last_deployment_url: ...})
│
└─ Réponse :
   {
     "deployment": {
       "deployment_id": "dpl_xxx",
       "full_url": "https://apihub-xxx.vercel.app",
       "project_name": "apihub-1234",
       "state": "READY",
       "elapsed_seconds": 12.3
     },
     "summary_md": "**Ton site est en ligne !** [https://...](https://...)"
   }
```

### 6.9 Diagramme de séquence — Website Builder (génération complète)

```
┌──────────┐  ┌──────────┐  ┌────────────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────┐
│  Client  │  │ FastAPI  │  │WebsiteBuilder       │  │ NVIDIA       │  │backend   │  │ Vercel │
│ Frontend │  │(backend- │  │Orchestrator         │  │ gpt-oss-120b │  │ api      │  │  API   │
│          │  │   ai)    │  │                     │  │              │  │          │  │        │
└────┬─────┘  └────┬─────┘  └──────────┬──────────┘  └──────┬───────┘  └────┬─────┘  └───┬────┘
     │              │                  │                     │               │             │
     │ POST /website/generate/stream   │                     │               │             │
     │─────────────►│                  │                     │               │             │
     │              │ stream_generate_website()              │               │             │
     │              │─────────────────►│                     │               │             │
     │              │                  │                     │               │             │
     │◄─────────── SSE: step "context" "loading" ───────────│               │             │
     │              │                  │ context_tool.fetch()                │             │
     │              │                  │─────────────────────────────────────►             │
     │              │                  │    brand_name, slogan, palette...   │             │
     │              │                  │◄─────────────────────────────────────             │
     │◄─────────── SSE: step "context" "done" ──────────────│               │             │
     │              │                  │                     │               │             │
     │◄─────────── SSE: step "design" "loading" ────────────│               │             │
     │              │                  │ generate_website_architecture()     │             │
     │              │                  │─────────────────────────────────────►             │
     │              │                  │  {sections, nav_links, animations}  │             │
     │              │                  │◄─────────────────────────────────────             │
     │              │                  │ generate_website_content()          │             │
     │              │                  │─────────────────────────────────────►             │
     │              │                  │  {sections: {hero: {...}, ...}}     │             │
     │              │                  │◄─────────────────────────────────────             │
     │◄─────────── SSE: step "design" "done" {sections: 4} ─│               │             │
     │              │                  │                     │               │             │
     │◄─────────── SSE: step "build" "loading" ─────────────│               │             │
     │              │                  │ build_website_html()                │             │
     │              │                  │────────────────────►│               │             │
     │              │                  │    HTML Tailwind+JS │               │             │
     │              │                  │◄────────────────────│               │             │
     │◄─────────── SSE: step "build" "done" ────────────────│               │             │
     │              │                  │                     │               │             │
     │◄─────────── SSE: step "qa" "loading" ────────────────│               │             │
     │              │                  │ validate_brand_identity()           │             │
     │              │                  │ validate_html_output()              │             │
     │              │                  │ [Si erreur → revise_website_html()] │             │
     │◄─────────── SSE: step "qa" "done" {sections, images} │               │             │
     │              │                  │                     │               │             │
     │◄─────────── SSE: step "persist" "loading" ───────────│               │             │
     │              │                  │ patch_website_project()             │             │
     │              │                  │─────────────────────────────────────►             │
     │              │                  │    {status: "generated", html}      │             │
     │              │                  │◄─────────────────────────────────────             │
     │◄─────────── SSE: step "persist" "done" ──────────────│               │             │
     │              │                  │                     │               │             │
     │◄─────────── SSE: result {context, description, html, html_stats} ────│             │
     │              │                  │                     │               │             │
     │ [Utilisateur clique "Déployer"] │                     │               │             │
     │ POST /website/deploy            │                     │               │             │
     │─────────────►│                  │                     │               │             │
     │              │ deploy_website() │                     │               │             │
     │              │─────────────────►│                     │               │             │
     │              │                  │ deploy_html_to_vercel()                           │
     │              │                  │────────────────────────────────────────────────►│
     │              │                  │   POST /v13/deployments {html}      │            │
     │              │                  │   {deployment_id, full_url, READY}  │            │
     │              │                  │◄────────────────────────────────────────────────│
     │              │                  │ patch_website_project(status="deployed", url)    │
     │              │ {full_url, deployment_id}              │               │             │
     │◄─────────────│                  │                     │               │             │
```

---

## 7. Tableau récapitulatif des outils

### 7.1 Outils par agent

| Agent | Outil | Type | API externe | Rôle |
|-------|-------|------|-------------|------|
| **NameAgent** | `generate_names` | LangChain tool | Azure OpenAI gpt-4o | Brainstorming de noms via LLM |
| **NameAgent** | `validate_names` | LangChain tool | **Brandfetch API** | Vérification disponibilité domaine/marque |
| **NameAgent** | Short-term memory | SQLite DB | — | Mémorisation noms déjà vérifiés |
| **SloganAgent** | `_call_llm` | Direct call | Azure OpenAI gpt-4o | Génération slogans en 1 appel |
| **SloganAgent** | `validate_minimal_slogans` | Validateur local | — | Parsing et normalisation JSON |
| **PaletteAgent** | `_call_llm` | Direct call | Azure OpenAI gpt-4o | Génération palettes en 1 appel |
| **PaletteAgent** | `validate_minimal_palettes` | Validateur local | — | Parsing et normalisation JSON |
| **LogoAgent** | `draft_logo_prompt` | LangChain tool | Azure OpenAI gpt-4.1 | Rédaction prompt image |
| **LogoAgent** | `render_logo_image` | LangChain tool | **HuggingFace Inference** | Génération image text-to-image |
| **LogoAgent** | `_remove_light_bg` | Post-traitement | rembg / PIL | Suppression du fond blanc |
| **LogoAgent** | `verifier_originalite` | Vérification | **SerpAPI Google Lens** | Reverse image search |
| **WebsiteBuilder** | `WebsiteContextTool` | HTTP client | backend-api REST | Chargement brand kit |
| **WebsiteBuilder** | `generate_architecture` | Direct LLM | NVIDIA gpt-oss-120b | Structure sections+animations |
| **WebsiteBuilder** | `generate_content` | Direct LLM | NVIDIA gpt-oss-120b | Textes de chaque section |
| **WebsiteBuilder** | `build_website_html` | Direct LLM | NVIDIA gpt-oss-120b | Code HTML/Tailwind/JS |
| **WebsiteBuilder** | `refine_description` | Direct LLM | NVIDIA gpt-oss-120b | Affinage selon retours |
| **WebsiteBuilder** | `revise_website_html` | Direct LLM | NVIDIA gpt-oss-120b | Modification chirurgicale HTML |
| **WebsiteBuilder** | `validate_brand_identity` | Validateur local | — | QA nom+slogan dans HTML |
| **WebsiteBuilder** | `validate_html_output` | Validateur local | — | QA navigation+images+responsive |
| **WebsiteBuilder** | `StepEmitter` | SSE emitter | — | Streaming temps réel |
| **WebsiteBuilder** | `deploy_html_to_vercel` | HTTP client | **Vercel API** | Déploiement production |
| **WebsiteBuilder** | `patch_website_project` | HTTP client | backend-api REST | Persistance état |

### 7.2 APIs externes par agent

| API externe | Agent(s) | Quota (free tier) | Authentification |
|-------------|----------|-------------------|------------------|
| **Azure OpenAI** (gpt-4o) | Name, Slogan, Palette | Selon abonnement | `AZURE_OPENAI_KEY` + endpoint |
| **Azure OpenAI** (gpt-4.1) | Logo | Selon abonnement | `AZURE_OPENAI_KEY` + deployment |
| **NVIDIA NIM** (gpt-oss-120b) | Website Builder | 40 req/min × 4 clés | `NVIDIA_API_KEY_1..4` |
| **Brandfetch API** | NameAgent | 100 req/mois gratuit | `BRANDFETCH_API_KEY` |
| **HuggingFace Inference** | LogoAgent | Modèle-dépendant | `HF_TOKEN_1..N` |
| **SerpAPI** (Google Lens) | LogoAgent | 100 req/mois gratuit | `SERPAPI_KEY` |
| **Vercel API** | Website Builder | Par déploiement | `VERCEL_TOKEN` |

---

## 8. Schéma d'enchaînement global du Brand Kit

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE COMPLET BRAND KIT → WEBSITE                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐
│        clarified_idea            │
│  {sector, target_users, problem, │
│   solution, country, language}   │
└───────────────┬──────────────────┘
                │
                ▼
┌──────────────────────────────────┐     Brandfetch API
│          NameAgent               │◄────────────────────
│  Architecture : LangGraph ReAct  │  vérification dispo
│  LLM : Azure gpt-4o (T=0.65)    │  noms de domaine
│  Outils : generate_names         │
│           validate_names         │
│  → 3 noms disponibles garantis   │
└───────────────┬──────────────────┘
                │ brand_name_chosen (sélection user)
                ▼
┌──────────────────────────────────┐
│         SloganAgent              │
│  Architecture : Appel LLM direct │
│  LLM : Azure gpt-4o (T=0.65)    │
│  → 3 slogans créatifs            │
└───────────────┬──────────────────┘
                │ slogan_options
                ▼
┌──────────────────────────────────┐
│         PaletteAgent             │
│  Architecture : Appel LLM direct │
│  LLM : Azure gpt-4o (T=0.65)    │
│  → 3 palettes (swatches hex)     │
└───────────────┬──────────────────┘
                │ color_palette (sélection user)
                ▼
┌──────────────────────────────────┐    HuggingFace   SerpAPI
│          LogoAgent               │◄──────────────   ──────────
│  Architecture : Appel LLM direct │  Qwen/Qwen-Image Google Lens
│  LLM : Azure gpt-4.1 (T=0.4)    │  génération img  originalité
│  Post-traitement : rembg / PIL   │
│  → Logo PNG transparent          │
└───────────────┬──────────────────┘
                │ brand_identity complet
                │ {name, slogan, palette, logo_b64}
                ▼
┌──────────────────────────────────────────────────────┐
│           WebsiteBuilderOrchestrator                  │
│  Architecture : Orchestrateur multi-phases (SSE)      │
│  LLM : NVIDIA gpt-oss-120b                           │
│                                                       │
│  Phase 1 → Contexte (WebsiteContextTool)             │
│  Phase 2A → Architecture (sections, animations)       │
│  Phase 2B → Contenu (textes de chaque section)       │
│  Phase 2.5 → Affinage (optionnel, sur retour user)   │
│  Phase 3 → HTML/Tailwind/JS complet                  │
│  Phase 4 → QA (brand identity + navigation + images) │
│  Déploiement → Vercel API                            │
│                                                       │
│  → Site vitrine en ligne sur *.vercel.app             │
└──────────────────────────────────────────────────────┘
```

---

## Références des fichiers sources

| Composant | Fichier |
|-----------|---------|
| Agent Nommage | `backend-ai/agents/branding/name_agent.py` |
| Agent Slogan | `backend-ai/agents/branding/slogan_agent.py` |
| Agent Palette | `backend-ai/agents/branding/palette_agent.py` |
| Agent Logo | `backend-ai/agents/branding/logo_agent.py` |
| Outils Nommage | `backend-ai/tools/branding/name_tools.py` |
| Outils Logo | `backend-ai/tools/branding/logo_tools.py` |
| Client image Logo | `backend-ai/tools/branding/logo_image_client.py` |
| Vérification originalité | `backend-ai/tools/branding/logo_originality_checker.py` |
| Orchestrateur Website | `backend-ai/agents/website_builder/orchestrator.py` |
| Outil Architecture | `backend-ai/tools/website_builder/architecture_tool.py` |
| Outil Contenu | `backend-ai/tools/website_builder/content_tool.py` |
| Outil HTML Builder | `backend-ai/tools/website_builder/coder_tool.py` |
| Outil Validation | `backend-ai/tools/website_builder/validator_tool.py` |
| Déploiement Vercel | `backend-ai/tools/website_builder/vercel_deploy.py` |
| Configuration Branding | `backend-ai/config/branding_config.py` |
| Validateurs partagés | `backend-ai/shared/branding/validators.py` |

---

*Rapport généré le 12 mai 2026 — Projet Brand AI (PFE)*
