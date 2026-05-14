# Diagrammes de Séquence — Brand Kit (PlantUML)

---

## Diagramme 1 — Agent de Nommage (ReAct)

```plantuml
@startuml Naming_Agent
title Agent de Nommage — Design Pattern ReAct

skinparam sequenceArrowThickness 2
skinparam ParticipantPadding 20
skinparam BoxPadding 10

actor       "Utilisateur"              as USER
participant "Frontend"                 as FE
participant "FastAPI"                  as API
participant "NameAgent\n(LangGraph ReAct)" as AG
participant "generate_names\n[LLM Tool]"  as GT
participant "validate_names\n[Brandfetch Tool]" as VT
participant "Azure gpt-4o"            as LLM
participant "Brandfetch API"          as BF
database    "SQLite\nMémoire court terme" as DB

USER -> FE  : Saisit ses préférences de nommage
FE  -> API  : POST /branding/name\n{clarified_idea, naming_preferences}
API -> AG   : run(state)

AG -> DB : load_exists_memory(idea_id)
DB --> AG : [noms déjà vérifiés comme existants]

loop Boucle ReAct — max 55 itérations

    note over AG : [THOUGHT]\nLe LLM raisonne :\ncombien de noms disponibles ?
    
    AG -> GT : generate_names(excluded_names)
    GT -> LLM : invoke(prompt + exclusions)
    LLM --> GT : {name_options: ["NomA", "NomB", ...]}
    GT --> AG : [OBSERVATION] noms générés

    AG -> VT : validate_names(name_options)
    loop Pour chaque nom proposé
        VT -> BF : GET /v2/search/{nom_normalisé}
        BF --> VT : {exists: true | false}
    end
    VT -> DB  : append_exists_memory(noms_existants)
    VT --> AG : [OBSERVATION] [{name, availability: "not_exists" | "exists"}]

    alt Moins de 3 noms disponibles
        AG -> AG : Continuer — régénérer avec exclusions mises à jour
    else 3 noms disponibles atteints
        AG -> AG : STOP — objectif atteint
    end

end

AG  --> API  : state { name_options: [...], status: "name_generated" }
API --> FE   : { name_options: [{ name, availability, description }] }
FE  --> USER : Affiche les propositions de noms
@enduml
```

---

## Diagramme 2 — Agent de Slogan

```plantuml
@startuml Slogan_Agent
title Agent de Slogan — Appel LLM Direct

skinparam sequenceArrowThickness 2
skinparam ParticipantPadding 20

actor       "Utilisateur"   as USER
participant "Frontend"      as FE
participant "FastAPI"       as API
participant "SloganAgent"   as AG
participant "Azure gpt-4o"  as LLM

USER -> FE  : Choisit un nom de marque\n+ définit ses préférences de ton
FE  -> API  : POST /branding/slogan\n{brand_name_chosen, clarified_idea, slogan_preferences}
API -> AG   : run(state)

AG -> AG : Vérifier la présence de brand_name_chosen

note over AG, LLM
    Contexte injecté dans le prompt :
    — Idée clarifiée (secteur, cible, problème, solution)
    — Nom de marque choisi par l'utilisateur
    — Préférences de ton (professionnel, inspirant, minimaliste…)
    — Langue cible
end note

AG -> LLM : ainvoke([SystemMessage, HumanMessage])
LLM --> AG : JSON brut { slogan_options: [...] }

AG -> AG : validate_minimal_slogans(raw)\nParsing JSON + vérification du nombre de slogans

AG  --> API  : state { slogan_options: [...], status: "slogan_generated" }
API --> FE   : { slogan_options: [{ slogan, vibe, language }] }
FE  --> USER : Affiche les propositions de slogans
@enduml
```

---

## Diagramme 3 — Agent de Palette de Couleurs

```plantuml
@startuml Palette_Agent
title Agent de Palette de Couleurs — Appel LLM Direct

skinparam sequenceArrowThickness 2
skinparam ParticipantPadding 20

actor       "Utilisateur"   as USER
participant "Frontend"      as FE
participant "FastAPI"       as API
participant "PaletteAgent"  as AG
participant "Azure gpt-4o"  as LLM

USER -> FE  : Confirme le nom de marque retenu
FE  -> API  : POST /branding/palette\n{brand_name_chosen, clarified_idea}
API -> AG   : run(state)

AG -> AG : Résoudre le nom de marque\nbrand_name_chosen → sinon premier de name_options

note over AG, LLM
    Contexte injecté dans le prompt :
    — Secteur d'activité et cible utilisateur
    — Nom de marque résolu
    — Pays et langue (conventions visuelles)
    — Nombre de palettes cibles : 3
end note

AG -> LLM : ainvoke([SystemMessage, HumanMessage])
LLM --> AG : JSON brut { palette_options: [...] }

AG -> AG : validate_minimal_palettes(raw)\nParsing + normalisation des swatches
AG -> AG : Extraire la palette principale\ncolor_palette = palette_options[0]

AG  --> API  : state { palette_options, color_palette, status: "palette_generated" }
API --> FE   : { palette_options: [{ palette_name, swatches: [{hex, usage}] }] }
FE  --> USER : Affiche les palettes de couleurs
@enduml
```

---

## Diagramme 4 — Agent de Logo

```plantuml
@startuml Logo_Agent
title Agent de Logo — Pipeline Multi-étapes

skinparam sequenceArrowThickness 2
skinparam ParticipantPadding 15

actor       "Utilisateur"        as USER
participant "Frontend"           as FE
participant "FastAPI"            as API
participant "LogoAgent"          as AG
participant "Azure gpt-4.1"      as LLM
participant "HuggingFace\nInference" as HF
participant "rembg / PIL"        as BG
participant "SerpAPI\nGoogle Lens"   as SERP

USER -> FE  : Choisit sa palette\n+ saisit ses remarques (optionnel)
FE  -> API  : POST /branding/logo\n{brand_name_chosen, palette_hint, logo_user_remarks}
API -> AG   : run(state)

AG -> AG : Vérifier brand_name_chosen\nConstruire feedback de régénération si applicable

== Phase 1 — Rédaction du prompt image ==

AG -> LLM : invoke([SystemMessage, HumanMessage])\n[nom + idée + palette + contraintes]
LLM --> AG : { "image_prompt": "...", "negative_prompt": "..." }
AG -> AG : Valider le prompt\n(longueur, nom présent, pas de #hex, pas de badge/frame)

== Phase 2 — Génération de l'image ==

AG -> HF : POST /models/Qwen/Qwen-Image\n{ inputs: image_prompt }
HF --> AG : image_bytes (PNG/JPEG)

== Phase 3 — Suppression du fond ==

AG -> BG : remove(image_bytes)
BG --> AG : transparent_bytes (PNG avec canal alpha)

== Phase 4 — Vérification d'originalité ==

loop max 2 tentatives

    AG -> SERP : Reverse image search\n{ image: transparent_bytes }
    SERP --> AG : { matches: [...], count: n }

    alt Logo suffisamment original (similaires ≤ 2)
        AG -> AG : Conserver le concept
    else Trop similaire à des logos existants
        AG -> LLM : invoke(prompt + feedback originalité)\n"Changer complètement l'icône et la composition"
        LLM --> AG : nouveau { image_prompt, negative_prompt }
        AG -> HF  : POST /models/Qwen/Qwen-Image\n{ inputs: nouveau_prompt }
        HF --> AG : nouveaux image_bytes
        AG -> BG  : remove(nouveaux image_bytes)
        BG --> AG : nouveaux transparent_bytes
    end

end

AG -> AG : Promouvoir la version transparente\ncomme image principale

AG  --> API  : state { logo_concepts: [...], status: "logo_generated" }
API --> FE   : { image_base64 (PNG transparent), image_prompt_used, image_provider }
FE  --> USER : Affiche le logo généré
@enduml
```

---

## Diagramme 5 — Vue Globale Brand Kit (avec refs)

```plantuml
@startuml Brand_Kit_Global
title Pipeline Brand Kit — Vue Globale

skinparam sequenceArrowThickness 2
skinparam ParticipantPadding 15
skinparam BoxPadding 10

actor       "Utilisateur"     as USER
participant "Frontend"        as FE
participant "FastAPI"         as API
participant "NameAgent"       as NA
participant "SloganAgent"     as SA
participant "PaletteAgent"    as PA
participant "LogoAgent"       as LA
database    "PipelineState\nbrand_identity" as STATE

== Étape 1 — Génération du nom de marque ==

USER -> FE  : Saisit ses préférences de nommage
FE  -> API  : POST /branding/name
API -> NA   : run(state)

ref over NA, STATE
  Diagramme 1 — Naming Agent
  ReAct Loop (LangGraph) :
  generate_names [Azure gpt-4o]
  validate_names [Brandfetch API]
  Mémoire court terme [SQLite]
end ref

NA  --> STATE : name_options [{ name, availability: "not_exists" }]
STATE --> FE  : Propositions de noms disponibles
USER -> FE   : Choisit un nom → brand_name_chosen

== Étape 2 — Génération du slogan ==

FE  -> API  : POST /branding/slogan
API -> SA   : run(state)

ref over SA, STATE
  Diagramme 2 — Slogan Agent
  Appel LLM direct [Azure gpt-4o]
  Contexte : idée + nom choisi + préférences
end ref

SA  --> STATE : slogan_options [{ slogan, vibe }]
STATE --> FE  : Propositions de slogans
USER -> FE   : Valide un slogan

== Étape 3 — Génération de la palette ==

FE  -> API  : POST /branding/palette
API -> PA   : run(state)

ref over PA, STATE
  Diagramme 3 — Palette Agent
  Appel LLM direct [Azure gpt-4o]
  Contexte : secteur + nom + pays + cible
end ref

PA  --> STATE : palette_options + color_palette [{ swatches: [{hex, usage}] }]
STATE --> FE  : Palettes de couleurs
USER -> FE   : Choisit une palette → palette_hint

== Étape 4 — Génération du logo ==

FE  -> API  : POST /branding/logo
API -> LA   : run(state)

ref over LA, STATE
  Diagramme 4 — Logo Agent
  Phase 1 : Prompt image [Azure gpt-4.1]
  Phase 2 : Génération image [HuggingFace]
  Phase 3 : Suppression fond [rembg/PIL]
  Phase 4 : Originalité [SerpAPI Google Lens]
end ref

LA  --> STATE : logo_concepts [{ image_base64 (PNG transparent) }]
STATE --> FE  : Logo PNG transparent

FE --> USER  : Brand Kit complet\n✓ Nom   ✓ Slogan   ✓ Palette   ✓ Logo
@enduml
```

---

## Notes de rendu

Ces diagrammes sont à générer via :
- **PlantUML Online** : https://www.plantuml.com/plantuml/uml/
- **VS Code** : extension *PlantUML* (Ctrl+Shift+P → Preview Current Diagram)
- **IntelliJ / PyCharm** : plugin *PlantUML Integration*
- **Ligne de commande** : `java -jar plantuml.jar DIAGRAMS_PLANTUML.md`
