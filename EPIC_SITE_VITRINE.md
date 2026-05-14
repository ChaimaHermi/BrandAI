# EPIC — Agent Website Builder : Génération de Site Vitrine

> **Branche :** `Rapport` | **Auteure :** Chaima Hermi | **Date :** 14 mai 2026

---

## Table des matières

1. [Objectifs de l'Epic](#1-objectifs-de-lepic)
2. [Choix du Modèle LLM](#2-choix-du-modèle-llm)
3. [Diagramme de Séquence](#3-diagramme-de-séquence)
4. [Implémentation](#4-implémentation)

---

## 1. Objectifs de l'Epic

### 1.1 Contexte et vision

À l'issue du pipeline de branding (nom, slogan, palette, logo), l'utilisateur dispose d'une identité visuelle complète pour sa startup. L'Epic **Website Builder** prolonge naturellement ce pipeline en offrant la génération **automatique et assistée** d'un site vitrine professionnel, prêt à être mis en ligne, sans que l'utilisateur ait à écrire une seule ligne de code.

L'objectif central est de réduire le temps de mise en ligne d'une startup de **plusieurs semaines à quelques minutes**, en s'appuyant exclusivement sur l'identité de marque déjà produite.

---

### 1.2 Fonctionnalités offertes par le site vitrine généré

Un site vitrine produit par l'agent est un **document HTML unique, auto-suffisant**, conçu pour présenter la startup à ses utilisateurs cibles. Il intègre les éléments suivants :

#### Sections de contenu

| Section | Contenu généré | Objectif marketing |
|---------|---------------|-------------------|
| **Hero** | Titre accrocheur, sous-titre, bouton CTA | Capter l'attention, pousser à l'action |
| **Fonctionnalités** | 3 à 6 cartes avec icônes Lucide, titres et descriptions | Expliquer la valeur produit |
| **Pourquoi nous** | Arguments différenciants, chiffres clés ou citations | Renforcer la confiance |
| **Pricing** *(optionnel)* | Plans tarifaires avec liste d'avantages | Déclencher la conversion |
| **Témoignages** *(optionnel)* | Citations clients, notes étoiles | Preuves sociales |
| **Contact** | Formulaire `mailto:` ou lien email, adresse sociale | Générer des leads |

#### Design et expérience utilisateur

- **Identité de marque intégrée** : nom de marque, slogan, logo (PNG transparent), couleurs exactes de la palette générée par l'agent Palette, typographies (Google Fonts).
- **Tailwind CSS via CDN** : design responsive et moderne sans fichier CSS externe.
- **Animations JavaScript** : effets `fade-in-up`, `slide-in-left`, etc., déclenchés au scroll (`IntersectionObserver`).
- **Navigation sticky** avec ancres `#id` valides, menu hamburger mobile.
- **Images avec fallback** : gestion du cas où une image distante est indisponible.
- **SEO de base** : `<meta charset>`, `<meta viewport>`, `<meta name="description">`, `<title>` personnalisés.
- **Responsive** : points de rupture Tailwind (`sm:`, `md:`, `lg:`), nav mobile.

#### Interactions utilisateur sur la plateforme Brand AI

Chaque fonctionnalité ci-dessous est décrite avec sa correspondance technique exacte dans le code.

---

**1. Génération du concept créatif**

L'orchestrateur `WebsiteBuilderOrchestrator` (`orchestrator.py`) appelle séquentiellement deux outils avant d'écrire le moindre HTML :

| Sous-étape | Outil | Fichier | Modèle | Config |
|-----------|-------|---------|--------|--------|
| Phase 2A — Structure | `generate_website_architecture()` | `architecture_tool.py` | `gpt-oss-120b` NVIDIA NIM | temp=0.5, max_tokens=2500 |
| Phase 2B — Contenu | `generate_website_content()` | `content_tool.py` | `gpt-oss-120b` NVIDIA NIM | temp=0.7, max_tokens=5000 |

- Prompt Phase 2A : `WEBSITE_ARCHITECTURE_SYSTEM` + `build_architecture_user_prompt(ctx)` → JSON `{sections, nav_links, animations, tone, language}`
- Prompt Phase 2B : `WEBSITE_CONTENT_SYSTEM` + `build_content_user_prompt(ctx, architecture)` → JSON `{sections: {hero: {headline, subheadline, cta_text}, features: {...}, ...}, meta: {title, description}}`
- Traçabilité LangSmith : tags `["website_builder", "tool", "phase_2a"]` / `"phase_2b"`
- Validation : `validate_architecture_payload()` vérifie min 4 sections + min 1 animation (`REQUIRED_SECTIONS_MIN=4`)

---

**2. Raffinement par chat (Phase 2.5)**

Route `POST /website/description/refine/stream` → `WebsiteBuilderOrchestrator.stream_refine_description()`

| Composant | Fichier | Rôle |
|-----------|---------|------|
| Outil | `refinement_tool.py` → `refine_website_description()` | Réécrit la description selon les retours utilisateur |
| Prompt système | `WEBSITE_DESCRIPTION_REFINE_SYSTEM` (`prompt_description_refinement.py`) | Cadre le LLM comme éditeur de concept |
| Prompt utilisateur | `build_description_refine_user_prompt(ctx, current_description, user_feedback)` | Injecte le JSON existant + l'instruction |
| Modèle | `gpt-oss-120b` NVIDIA NIM | temp=0.7, max_tokens=4000 (`DESCRIPTION_TEMPERATURE`, `DESCRIPTION_MAX_TOKENS`) |
| Validation sortie | `validate_description_payload()` (`validator_tool.py`) | Vérifie structure JSON description |
| Streaming | `StepEmitter` → event `{"type":"step","id":"refine","status":"running"}` | `step_streamer.py` |

Ticks live affichés pendant l'appel LLM (définis dans `step_streamer.py`) :
```python
REFINEMENT_TICKS = (
    "Lecture attentive de tes retours...",
    "Identification des sections impactées...",
    "Réécriture du concept hero si nécessaire...",
    "Ajustement des sections / animations...",
    "Maintien de la cohérence avec la marque...",
    "Validation du nouveau JSON...",
)
```

---

**3. Approbation avant génération**

Route `POST /website/description/approve` → pas de LLM, pure persistance :

| Composant | Fichier | Action |
|-----------|---------|--------|
| Outil persistance | `patch_website_project()` | `website_project_persistence.py` → `PATCH /website-projects/{id}` sur backend-api |
| Payload | `{"approved": True, "description_json": description}` | Marque le concept comme validé en base |
| Suite | Frontend → appelle immédiatement `apiStreamGenerateWebsite()` | Transition de phase `description_ready → generating` |

---

**4. Streaming live (SSE)**

Composant central : `StepEmitter` (`step_streamer.py`) — couche XAI du pipeline.

| Événement SSE | Déclenchement | Contenu |
|---------------|--------------|---------|
| `{"type":"step","id":"X","status":"running"}` | Début de chaque phase | id = `context`, `design`, `build`, `qa`, `persist` |
| `{"type":"tick","id":"X","label":"..."}` | Toutes les N secondes pendant attente LLM | Messages créatifs de `DESCRIPTION_TICKS` / `GENERATION_TICKS` |
| `{"type":"code_chunk","content":"..."}` | Chaque chunk SSE de GLM-5.1 (Phase 3) | Fragment HTML brut relayé en temps réel |
| `{"type":"step","id":"X","status":"done","meta":{}}` | Fin de chaque phase | meta = stats (sections, images, links) |
| `{"type":"result","payload":{}}` | Fin du pipeline complet | html, html_stats, description, context |
| `{"type":"error","message":"..."}` | Exception non récupérable | Message d'erreur propagé au frontend |

Côté FastAPI : `StreamingResponse(content=generator, media_type="text/event-stream")`.  
Côté frontend (`websiteBuilder.api.js`) : parsing ligne par ligne via `EventSource` ou `fetch + ReadableStream`.

---

**5. Preview interactif**

Composant frontend : `PreviewPanel.jsx` — l'HTML généré est rendu dans un `<iframe sandbox>`.

| Mécanisme | Fichier | Détail |
|-----------|---------|--------|
| Normalisation HTML | `normalizeWebsiteHtml()` | `useWebsiteBuilder.js` — enveloppe les fragments dans un `<!DOCTYPE html>` complet si nécessaire |
| Nettoyage artefacts | `sanitizePreviewArtifacts()` | Retire les scripts d'injection entre marqueurs `BRANDAI_PREVIEW_INJECTION_START/END` |
| Strip scripts | `stripInjectedScripts()` + `stripLeakedInjectedScripts()` | Supprime les scripts d'édition qui auraient "fui" hors balise `<script>` |
| Communication | `postMessage` bidirectionnel | `BRANDAI_PREVIEW_READY`, `BRANDAI_EDIT_MODE_ON/OFF`, `BRANDAI_HTML_UPDATE`, `BRANDAI_REQUEST_HTML` |

---

**6. Révision par chat (Phase 4)**

Route `POST /website/revise/stream` → `WebsiteBuilderOrchestrator.stream_revise_website()`

| Composant | Fichier | Rôle |
|-----------|---------|------|
| Outil | `revision_tool.py` → `revise_website_html()` | Modification chirurgicale du HTML existant |
| Prompt système | `WEBSITE_REVISION_SYSTEM` (`prompt_website_revision.py`) | LLM positionné comme chirurgien HTML |
| Prompt utilisateur | `build_website_revision_user_prompt(ctx, current_html, instruction)` | Injecte HTML complet + instruction ciblée |
| Modèle | `gpt-oss-120b` NVIDIA NIM | temp=0.3, max_tokens=32000 (`REVISION_TEMPERATURE`, `REVISION_MAX_TOKENS`) |
| Post-traitement | `extract_html_document()` + `repair_html_document()` | `website_renderer.py` — extrait et répare le HTML retourné |
| Erreurs transitoires | `_is_transient_provider_error()` | Détecte 502/503/504 Nginx/Vercel sans retry (SDK gère ses retries) |
| Traçabilité | LangSmith tag `phase_4` | `process_revision_inputs / process_revision_outputs` |

---

**7. Édition in-place**

Mode édition entièrement côté frontend, sans appel LLM.

| Mécanisme | Fichier | Détail |
|-----------|---------|--------|
| Activation | `PreviewPanel.jsx` → `postMessage("BRANDAI_EDIT_MODE_ON")` | Injecte `contenteditable="true"` + `data-brandai-editable="1"` sur tous les nœuds texte |
| Récupération HTML | `postMessage("BRANDAI_REQUEST_HTML")` → `BRANDAI_HTML_UPDATE` | L'iframe renvoie son `document.documentElement.outerHTML` |
| Nettoyage | `sanitizePreviewArtifacts(rawHtml)` | Retire les attributs `contenteditable`, `data-brandai-editable`, scripts d'injection |
| Sauvegarde | `apiSaveWebsiteHtml()` → `POST /website/save` | `websiteBuilder.api.js` → orchestrateur → `patch_website_project({current_html: html})` |
| Transition phase | `saving_edits → ready` | `useWebsiteBuilder.js` |

---

**8. Déploiement 1 clic (Phase 5)**

Route `POST /website/deploy` → `WebsiteBuilderOrchestrator.deploy_website()`

| Composant | Fichier | Détail |
|-----------|---------|--------|
| Validation préalable | `validate_html_document(html)` | `website_renderer.py` — vérifie `<html>`, `<body>`, `</html>` |
| Outil déploiement | `deploy_html_to_vercel(html, idea_id, brand_name)` | `vercel_deploy.py` |
| Appel API | `POST https://api.vercel.com/v13/deployments` | Auth : `Bearer {VERCEL_API_KEY}` — payload : `{name, files:[{file:"index.html", data:html}]}` |
| Polling | Toutes les 2.5 s (`VERCEL_POLL_INTERVAL_SECONDS`) | Jusqu'à `state=="READY"` ou timeout 180 s (`VERCEL_POLL_TIMEOUT_SECONDS`) |
| Persistance résultat | `patch_website_project({status:"deployed", last_deployment_url, last_deployment_id})` | `website_project_persistence.py` |
| Réponse frontend | `{deployment_id, full_url, project_name, state:"READY", elapsed_seconds}` | Affiché comme badge vert "En ligne" dans le header |

---

**9. Persistance de session**

Deux outils de persistance utilisés en fin de chaque phase par l'orchestrateur :

| Outil | Fichier | Route backend-api | Moment d'appel |
|-------|---------|------------------|----------------|
| `patch_website_project()` | `website_project_persistence.py` | `PATCH /website-projects/{idea_id}` | Après Phase 2 (description), Phase 3 (HTML), Phase 4 (révision), Phase 5 (deploy) |
| `append_website_message()` | `website_project_persistence.py` | `POST /website-projects/{idea_id}/messages` | Après chaque résultat significatif (génération, révision, déploiement) |

Côté frontend, `bootstrapFromPersistence()` (`useWebsiteBuilder.js`) exécute au mount :
1. `apiFetchWebsiteProject()` → restaure `description_json`, `current_html`, `last_deployment_url`, `conversation_json`
2. `apiFetchWebsiteContext()` → restaure le contexte brand kit
3. `derivePhaseFromProject(project)` → recalcule la phase courante (`context_ready`, `description_ready`, `ready`, `deployed`)
4. `ensureResumeGuidance(messages, phase)` → injecte un message de reprise avec les actions appropriées selon la phase

---

### 1.3 Critères d'acceptation

- [ ] Le site généré contient le nom de marque et le slogan verbatim.
- [ ] La palette de couleurs de l'agent Palette est appliquée.
- [ ] Le site est responsive (mobile + desktop).
- [ ] La navigation par ancres fonctionne sans `href="#"` nu.
- [ ] Le déploiement Vercel retourne une URL accessible publiquement.
- [ ] La reprise de session restaure le HTML et le concept sans re-génération.
- [ ] Les révisions par chat modifient uniquement les éléments ciblés.

---

## 2. Choix du Modèle LLM

### 2.1 Contraintes techniques

Le Website Builder impose des contraintes spécifiques à chaque phase :

| Phase | Contrainte principale | Impact sur le choix du modèle |
|-------|-----------------------|-------------------------------|
| Phase 2A — Architecture | Sortie JSON structurée, courte (~1 k tokens) | Modèle rapide, bon suivi d'instructions |
| Phase 2B — Contenu | Sortie mixte JSON + texte créatif (~4 k tokens) | Créativité + cohérence sémantique |
| Phase 3 — HTML | Code long (8 k–20 k tokens), déterministe | Fenêtre de sortie étendue, génération code |
| Phase 4 — Révision | Modification chirurgicale sur un HTML existant | Capacité de diff, fenêtre d'entrée longue |

### 2.2 Architecture multi-modèles retenue

Le pipeline Website Builder utilise **deux familles de modèles** selon la phase :

```
Phase 2A ─► openai/gpt-oss-120b  (NVIDIA NIM)   ── Architecture JSON
Phase 2B ─► openai/gpt-oss-120b  (NVIDIA NIM)   ── Contenu textuel
Phase 2.5─► openai/gpt-oss-120b  (NVIDIA NIM)   ── Raffinement concept
Phase 3  ─► z-ai/glm-5.1         (NVIDIA NIM)   ── Génération HTML/CSS/JS ← MODÈLE DÉDIÉ CODE
Phase 4  ─► openai/gpt-oss-120b  (NVIDIA NIM)   ── Révision chirurgicale
```

#### Modèle principal — `openai/gpt-oss-120b` (NVIDIA NIM)

| Paramètre | Valeur |
|-----------|--------|
| Fournisseur | NVIDIA NIM |
| Fenêtre d'entrée | 128 k tokens |
| Fenêtre de sortie | 65 k tokens |
| Température Phase 2A | 0.5 |
| Température Phase 2B | 0.7 |
| Max tokens Phase 2A | 2 500 |
| Max tokens Phase 2B | 5 000 |

**Justification :** `gpt-oss-120b` est un modèle de 120 milliards de paramètres à très large contexte (128k). Sa fenêtre étendue est indispensable pour ingérer le brand kit complet (nom, slogan, palette, logo en base64, idée clarifiée) en un seul appel. Sa capacité de raisonnement JSON structuré garantit des architectures cohérentes et des contenus alignés sur le positionnement de la marque.

**Rotation des clés :** 4 clés API NVIDIA (`NVIDIA_API_KEY_1` à `NVIDIA_API_KEY_4`) sont gérées par le `BaseAgent` pour contourner les rate limits (40 req/min par clé).

#### Modèle dédié code — `z-ai/glm-5.1` (NVIDIA NIM)

| Paramètre | Valeur |
|-----------|--------|
| Fournisseur | NVIDIA NIM |
| Température | 0.3 |
| Max tokens | 24 000 |
| Streaming SSE | Activé (chunks `content` + `reasoning`) |

**Justification :** GLM-5.1 est un modèle spécialisé dans la génération de code. Sa température basse (0.3) produit un HTML déterministe et syntaxiquement correct. Sa large fenêtre de sortie (24k tokens) permet de générer des pages riches sans troncature. Le streaming SSE natif de NVIDIA NIM permet de relayer chaque chunk HTML au frontend en temps réel, donnant à l'utilisateur une expérience de génération "live".

### 2.3 Comparatif des alternatives évaluées

| Modèle | Avantage | Limite | Décision |
|--------|----------|--------|----------|
| `gpt-4o` Azure | Qualité de raisonnement | Fenêtre de sortie limitée (4k), coût élevé | Utilisé pour le branding, pas le website |
| `gpt-4.1` Azure | Qualité code | Quota limité | Réservé au LogoAgent |
| `claude-3.5-sonnet` | Excellente génération HTML | Pas disponible via NIM, coût API | Non retenu |
| `z-ai/glm-5.1` NIM | 24k tokens sortie, streaming, code | Moins créatif que gpt-oss | **Retenu Phase 3** |
| `openai/gpt-oss-120b` NIM | 128k/65k contexte, JSON structuré | Moins performant sur le code pur | **Retenu Phase 2+4** |

---

## 3. Diagramme de Séquence

### 3.1 Vue d'ensemble — Pipeline complet Website Builder

Le diagramme ci-dessous représente le flux complet depuis l'arrivée de l'utilisateur sur la page Website Builder jusqu'à l'obtention de l'URL Vercel.

```
Acteurs :
  U   = Utilisateur (Frontend React)
  FE  = Frontend (WebsiteBuilderPage + useWebsiteBuilder)
  API = FastAPI Backend-AI (routes /website/*)
  CTX = WebsiteContextTool (fetche brand kit depuis backend-api)
  LLM = NVIDIA NIM (gpt-oss-120b / glm-5.1)
  DB  = backend-api (persistance : WebsiteProject)
  VCL = Vercel API
```

```
U          FE              API              CTX/LLM            DB            VCL
│          │               │                    │               │              │
│ Ouvre    │               │                    │               │              │
│ /website │               │                    │               │              │
│─────────►│               │                    │               │              │
│          │ bootstrapFromPersistence()          │               │              │
│          │──────────────►│ GET /website/project│               │              │
│          │               │────────────────────────────────────►│              │
│          │               │       {current_html, description_json, ...}        │
│          │               │◄────────────────────────────────────│              │
│          │ [Si état sauvegardé : restaure HTML + phase]        │              │
│          │◄──────────────│               │                    │               │
│          │               │               │                    │               │
│          │ loadContext() │               │                    │               │
│          │──────────────►│ GET /website/context               │               │
│          │               │───────────────────►│               │               │
│          │               │  GET /ideas/{id}   │               │               │
│          │               │  GET /brand-identity/{id}          │               │
│          │               │◄───────────────────│               │               │
│          │ {brand_name, slogan, palette, logo_url, ...}        │               │
│          │◄──────────────│               │                    │               │
│          │ [Phase = context_ready]        │                    │               │
│          │               │               │                    │               │
│ Clique   │               │               │                    │               │
│ "Générer │               │               │                    │               │
│  la desc"│               │               │                    │               │
│─────────►│               │               │                    │               │
│          │ apiStreamWebsiteDescription()  │                    │               │
│          │──────────────►│ POST /website/description/stream   │               │
│          │               │               │                    │               │
│          │◄── SSE: step "design" loading ─│                    │               │
│          │               │ generate_website_architecture(ctx) │               │
│          │               │───────────────────────────────────►│               │
│          │               │  {sections:[hero,features,...],    │               │
│          │               │   nav_links, animations, tone}     │               │
│          │               │◄───────────────────────────────────│               │
│          │               │ generate_website_content(ctx, arch)│               │
│          │               │───────────────────────────────────►│               │
│          │               │  {sections:{hero:{headline,...},   │               │
│          │               │            features:{...}, ...}}   │               │
│          │               │◄───────────────────────────────────│               │
│          │◄── SSE: step "design" done ────│                    │               │
│          │◄── SSE: result {description, description_summary_md}│               │
│          │ [Phase = description_ready]    │                    │               │
│          │               │               │                    │               │
│ [Optionnel] Raffine le concept via chat   │                    │               │
│ "Ajoute  │               │               │                    │               │
│  pricing"│               │               │                    │               │
│─────────►│               │               │                    │               │
│          │ apiStreamRefineWebsiteDescription()                 │               │
│          │──────────────►│ POST /website/description/refine/stream             │
│          │               │ {description, instruction}         │               │
│          │               │ refine_website_description(...)    │               │
│          │               │───────────────────────────────────►│               │
│          │               │  {description mis à jour}          │               │
│          │               │◄───────────────────────────────────│               │
│          │◄── SSE: result {description updated} ──────────────│               │
│          │ [Phase = description_ready]    │                    │               │
│          │               │               │                    │               │
│ Clique   │               │               │                    │               │
│ "J'approu│               │               │                    │               │
│  ve"     │               │               │                    │               │
│─────────►│               │               │                    │               │
│          │ apiApproveWebsiteDescription()│                    │               │
│          │──────────────►│ POST /website/description/approve  │               │
│          │               │────────────────────────────────────►│              │
│          │               │  {approved: true}                  │               │
│          │               │◄────────────────────────────────────│              │
│          │◄──────────────│               │                    │               │
│          │               │               │                    │               │
│          │ apiStreamGenerateWebsite()     │                    │               │
│          │──────────────►│ POST /website/generate/stream      │               │
│          │               │               │                    │               │
│          │◄── SSE: step "build" loading ──│                    │               │
│          │               │ build_website_html(ctx, arch, content)              │
│          │               │──────────────── glm-5.1 ──────────►│               │
│          │               │  [STREAMING] chunks HTML live      │               │
│          │◄── SSE: code_chunk {content: "<div..."} ──────────►│               │
│          │◄── SSE: code_chunk {content: "..."} ───────────────│               │
│          │               │  HTML Tailwind/JS complet (8-20k)  │               │
│          │               │◄──────────────────────────────────────              │
│          │◄── SSE: step "build" done ─────│                    │               │
│          │               │               │                    │               │
│          │◄── SSE: step "qa" loading ─────│                    │               │
│          │               │ validate_brand_identity(html)      │               │
│          │               │ validate_html_output(html)         │               │
│          │               │ sanitize_navigation_html(html)     │               │
│          │               │ [Si erreur → revise_website_html() LLM correction] │
│          │◄── SSE: step "qa" done {sections:5, images:3} ─────│               │
│          │               │               │                    │               │
│          │◄── SSE: step "persist" loading │                    │               │
│          │               │ patch_website_project(idea_id, {html, status})     │
│          │               │────────────────────────────────────►│              │
│          │               │  {id, status: "generated"}         │               │
│          │               │◄────────────────────────────────────│              │
│          │◄── SSE: step "persist" done ───│                    │               │
│          │◄── SSE: result {html, html_stats, description} ─────│               │
│          │ [Phase = ready — HTML dans iframe]                  │               │
│          │               │               │                    │               │
│ [Optionnel] Révise le site par chat                            │               │
│ "Rends le│               │               │                    │               │
│  hero    │               │               │                    │               │
│  sombre" │               │               │                    │               │
│─────────►│               │               │                    │               │
│          │ apiStreamReviseWebsite()       │                    │               │
│          │──────────────►│ POST /website/revise/stream        │               │
│          │               │ {currentHtml, instruction}         │               │
│          │               │ revise_website_html(ctx, html, instruction)        │
│          │               │──────────────── gpt-oss-120b ─────►│               │
│          │               │  HTML révisé (diff chirurgical)    │               │
│          │               │◄───────────────────────────────────│               │
│          │◄── SSE: result {html révisé} ──│                    │               │
│          │ [Preview mis à jour]           │                    │               │
│          │               │               │                    │               │
│ Clique   │               │               │                    │               │
│ "Déployer│               │               │                    │               │
│  Vercel" │               │               │                    │               │
│─────────►│               │               │                    │               │
│          │ apiDeployWebsite()             │                    │               │
│          │──────────────►│ POST /website/deploy               │               │
│          │               │ validate_html_document(html)       │               │
│          │               │ deploy_html_to_vercel(html, idea_id, brand_name)   │
│          │               │────────────────────────────────────────────────────►
│          │               │  POST /v13/deployments             │              │
│          │               │  {name: "brandai-42",              │              │
│          │               │   files: [{path:"index.html",...}]}│              │
│          │               │   [Polling VERCEL_POLL_INTERVAL=2.5s]             │
│          │               │  {deployment_id, full_url, state: "READY"}        │
│          │               │◄────────────────────────────────────────────────────
│          │               │ patch_website_project(status="deployed", url)     │
│          │               │────────────────────────────────────►│              │
│          │ {deployment:{full_url:"https://brandai-42.vercel.app"}}            │
│          │◄──────────────│               │                    │               │
│ [Phase = deployed — lien live en header] │                    │               │
│◄─────────│               │               │                    │               │
```

---

### 3.2 Diagramme de séquence — Phase 3 (Génération HTML avec streaming GLM-5.1)

Ce sous-diagramme détaille la communication SSE entre le frontend et le backend pendant la génération du code HTML.

```
Frontend                FastAPI              NVIDIA NIM (glm-5.1)
(EventSource)           (StreamingResponse)
    │                       │                        │
    │  POST /generate/stream │                        │
    │──────────────────────►│                        │
    │                       │  POST /chat/completions │
    │                       │  {model: "z-ai/glm-5.1",│
    │                       │   stream: true,         │
    │                       │   messages: [system,    │
    │                       │              user(arch+ │
    │                       │              content)]} │
    │                       │───────────────────────►│
    │                       │                        │ [Génération]
    │  event: step           │                        │
    │  data: {id:"build",    │                        │
    │         status:"loading"}                       │
    │◄──────────────────────│                        │
    │                       │  data: {"choices":[{"delta":{"content":"<!DOCTYPE"}}]}
    │                       │◄───────────────────────│
    │  event: code_chunk     │                        │
    │  data: {content:"<!DOCTYPE html>"}              │
    │◄──────────────────────│                        │
    │                       │  data: {"choices":[{"delta":{"content":"<html"}}]}
    │                       │◄───────────────────────│
    │  event: code_chunk     │                        │
    │  data: {content:"<html lang=\"fr\">"}           │
    │◄──────────────────────│                        │
    │         ... (N chunks) ...                      │
    │                       │  data: [DONE]           │
    │                       │◄───────────────────────│
    │  event: step           │                        │
    │  data: {id:"build",    │                        │
    │         status:"done"} │                        │
    │◄──────────────────────│                        │
    │  event: result         │                        │
    │  data: {html:"...",    │                        │
    │         html_stats:{}} │                        │
    │◄──────────────────────│                        │
```

---

## 4. Implémentation

### 4.1 Architecture globale

```
backend-ai/
├── agents/
│   └── website_builder/
│       └── orchestrator.py          ← Chef d'orchestre, 5 phases
├── tools/
│   └── website_builder/
│       ├── context_tool.py          ← Phase 1 : fetch brand kit
│       ├── architecture_tool.py     ← Phase 2A : structure sections
│       ├── content_tool.py          ← Phase 2B : contenu textuel
│       ├── coder_tool.py            ← Phase 3 : HTML/Tailwind/JS (GLM-5.1)
│       ├── refinement_tool.py       ← Phase 2.5 : affinage concept
│       ├── revision_tool.py         ← Phase 4 : révision chirurgicale
│       ├── validator_tool.py        ← QA : brand identity + HTML
│       ├── vercel_deploy.py         ← Phase 5 : déploiement Vercel
│       ├── step_streamer.py         ← Émetteur SSE (StepEmitter)
│       └── website_project_persistence.py ← Persistance état
├── config/
│   └── website_builder_config.py   ← Paramètres modèles par phase
└── prompts/
    └── website_builder/
        ├── prompt_architecture.py
        ├── prompt_content.py
        ├── prompt_coder.py
        ├── prompt_refinement.py
        └── prompt_revision.py

frontend/src/agents/website/
├── pages/
│   └── WebsiteBuilderPage.jsx       ← Layout split : ChatPanel + PreviewPanel
├── hooks/
│   └── useWebsiteBuilder.js         ← Machine à états (phases 1→5)
├── components/
│   ├── ChatPanel.jsx                ← Fil de conversation + boutons d'action
│   ├── ChatMessage.jsx              ← Rendu messages (stream, JSON, context)
│   ├── PreviewPanel.jsx             ← iframe + mode édition + déploiement
│   └── ChatInput.jsx                ← Zone de saisie
└── api/
    └── websiteBuilder.api.js        ← Fonctions fetch + SSE parsers
```

### 4.2 Machine à états frontend (useWebsiteBuilder)

Le hook `useWebsiteBuilder` gère les **11 phases** du cycle de vie :

```
idle
  │ (chargement au mount)
  ▼
loading_context → [erreur] → error
  │
  ▼
context_ready
  │ (clic "Générer la description")
  ▼
describing → [erreur] → context_ready
  │
  ▼
description_ready ←──────────────────────┐
  │ (chat pour affiner)                  │
  ▼                                      │
refining ─────────────────────────────────┘
  │ (clic "J'approuve")
  ▼
generating → [erreur] → description_ready
  │
  ▼
ready ◄────────────────────────────────────┐
  │ (chat pour réviser)                    │
  ▼                                        │
revising ──────────────────────────────────┘
  │ (édition manuelle)
  ▼
saving_edits → ready
  │ (clic "Déployer")
  ▼
deploying → [erreur] → ready
  │
  ▼
deployed
```

### 4.3 Phase 1 — Chargement du contexte

**Fichier :** `tools/website_builder/context_tool.py`

Le `WebsiteContextTool` agrège en un seul appel les données nécessaires à la génération :

```python
class WebsiteContext:
    idea_id: int
    brand_name: str          # ex: "APIHub"
    slogan: str              # ex: "One API, Infinite Possibilities"
    sector: str              # ex: "SaaS / Intégration API"
    target_audience: str
    short_pitch: str
    language: str            # "fr" ou "en"
    primary_color: str       # "#0066FF"
    secondary_color: str     # "#001166"
    accent_color: str        # "#FF6600"
    background_color: str    # "#FFFFFF"
    text_color: str          # "#111111"
    logo_url: str            # URL ou data:image/png;base64,...
    title_font: str          # "Playfair Display"
    body_font: str           # "Inter"
    visual_style: str        # "modern-minimal"
```

Le logo est normalisé en `data:image/png;base64,...` pour être embarqué directement dans le HTML (pas de dépendance externe). Un timeout de **8 secondes** (`WEBSITE_CONTEXT_LOGO_NORMALIZE_TIMEOUT_SECONDS`) garantit que cette étape ne bloque pas la suite si l'URL logo est lente.

### 4.4 Phase 2A — Génération de l'architecture

**Fichier :** `tools/website_builder/architecture_tool.py`  
**Modèle :** `openai/gpt-oss-120b` (temp=0.5, max_tokens=2500)

Le LLM génère une structure JSON décrivant les sections du site :

```json
{
  "sections": [
    {"id": "hero",     "type": "hero",     "purpose": "Accrocher l'utilisateur"},
    {"id": "features", "type": "features", "purpose": "Présenter les 4 fonctions clés"},
    {"id": "pricing",  "type": "pricing",  "purpose": "Afficher les 3 plans tarifaires"},
    {"id": "contact",  "type": "contact",  "purpose": "Formulaire email + LinkedIn"}
  ],
  "nav_links":  ["#features", "#pricing", "#contact"],
  "animations": ["fade-in-up", "slide-in-left"],
  "visual_style": "modern-minimal",
  "tone": "professionnel et accessible",
  "language": "fr"
}
```

**Garde-fous :** minimum 4 sections (`REQUIRED_SECTIONS_MIN=4`), minimum 1 animation (`REQUIRED_ANIMATIONS_MIN=1`).

### 4.5 Phase 2B — Génération du contenu

**Fichier :** `tools/website_builder/content_tool.py`  
**Modèle :** `openai/gpt-oss-120b` (temp=0.7, max_tokens=5000)

Le LLM remplit chaque section avec du texte réel aligné sur la marque :

```json
{
  "sections": {
    "hero": {
      "headline": "Une API pour les unifier toutes",
      "subheadline": "Simplifiez vos intégrations avec APIHub en moins de 10 minutes",
      "cta_text": "Commencer gratuitement",
      "cta_href": "#contact"
    },
    "features": {
      "title": "Pourquoi choisir APIHub ?",
      "items": [
        {"icon": "Zap",      "title": "Connexion instantanée", "desc": "..."},
        {"icon": "Shield",   "title": "Sécurité renforcée",    "desc": "..."},
        {"icon": "BarChart", "title": "Monitoring temps réel", "desc": "..."}
      ]
    }
  },
  "meta": {
    "title": "APIHub — Intégrations API unifiées",
    "description": "Connectez vos outils en quelques minutes avec APIHub."
  }
}
```

**Icônes :** Le modèle utilise exclusivement le jeu d'icônes **Lucide** (chargé via CDN) pour garantir la disponibilité côté client.

### 4.6 Phase 3 — Génération HTML/CSS/JS (coder)

**Fichier :** `tools/website_builder/coder_tool.py`  
**Modèle :** `z-ai/glm-5.1` (temp=0.3, max_tokens=24000, **streaming activé**)

C'est la phase la plus complexe. Le LLM reçoit en entrée :
- Le `WebsiteContext` complet (brand kit)
- L'architecture JSON (Phase 2A)
- Le contenu JSON (Phase 2B)

Et produit un **fichier HTML unique** contenant :

```
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{meta.title}</title>
  <meta name="description" content="{meta.description}" />
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family={title_font}&family={body_font}" rel="stylesheet" />
  <script>tailwind.config = { theme: { extend: { colors: { primary: "{primary_color}", ... } } } }</script>
  <style>/* animations CSS */</style>
</head>
<body>
  <!-- Navigation sticky avec menu hamburger mobile -->
  <nav>...</nav>

  <!-- Sections générées dynamiquement -->
  <section id="hero">...</section>
  <section id="features">...</section>
  ...

  <!-- Script d'animation IntersectionObserver -->
  <script>
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.1 });
    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
  </script>
</body>
</html>
```

**Streaming SSE :** Chaque chunk `content` produit par GLM-5.1 est immédiatement relayé au frontend via un événement `code_chunk`. L'utilisateur voit le code apparaître caractère par caractère dans la carte de progression du chat.

**Gestion des erreurs transitoires :** Les erreurs 502/503/504 (Bad Gateway, Gateway Timeout) du provider sont détectées et propagées avec un message explicite plutôt que réessayées (le SDK gère ses propres retries).

**Post-traitement du HTML :**
```python
def _post_process_html(raw: str) -> str:
    html = extract_html_document(raw)      # extrait <!DOCTYPE...></html>
    html = repair_html_document(html)      # ferme les balises ouvertes
    html = _replace_platform_emails(html)  # remplace "support@brandai" par email startup
    return html
```

### 4.7 Phase QA — Validation automatique

**Fichier :** `tools/website_builder/validator_tool.py`

La validation s'exécute systématiquement après la génération :

```
validate_brand_identity(html, brand_name, slogan)
    ├─ brand_name présent verbatim ? → RuntimeError sinon
    └─ slogan présent verbatim ?     → RuntimeError sinon

sanitize_navigation_html(html)
    └─ Remplace tous les href="#" nus par href="#hero"

validate_html_output(html)
    ├─ Vérifie <meta name="viewport">
    ├─ Vérifie présence de classes sm:/md:/lg: (responsive)
    ├─ Vérifie que tous les href="#anchor" ont un id="anchor" correspondant
    ├─ Vérifie que les <img> ont un attribut alt
    └─ Retourne stats : {sections, images, links, ok}

[Si erreur QA] → auto-correction :
    revise_website_html(ctx, html, "Fix: {liste des erreurs QA}", invoke_llm)
    → LLM corrige uniquement les problèmes détectés
    → Revalidation immédiate (1 seul retry)
```

### 4.8 Phase 4 — Révision par chat

**Fichier :** `tools/website_builder/revision_tool.py`  
**Modèle :** `openai/gpt-oss-120b` (temp=0.3, max_tokens=32000)

L'utilisateur envoie une instruction en langage naturel. Le LLM reçoit le HTML existant + l'instruction et retourne le HTML complet modifié. Le principe de **révision chirurgicale** signifie que seuls les éléments ciblés sont modifiés, le reste du site est conservé intact.

```
Exemple d'instruction : "Rends le hero plus sombre et ajoute un compte à rebours"

Entrée :  currentHtml (8-15k tokens) + instruction
Sortie :  HTML révisé (même structure, section hero modifiée uniquement)
```

### 4.9 Phase 5 — Déploiement Vercel

**Fichier :** `tools/website_builder/vercel_deploy.py`

```python
payload = {
    "name": f"brandai-{idea_id}",
    "files": [
        {
            "file": "index.html",
            "data": html,              # Contenu HTML brut
            "encoding": "utf-8"
        }
    ],
    "projectSettings": {
        "framework": None              # Site statique HTML pur
    }
}

# POST https://api.vercel.com/v13/deployments
# Authorization: Bearer {VERCEL_API_KEY}
response = httpx.post(VERCEL_API_BASE + "/v13/deployments", json=payload, headers=headers)

# Polling jusqu'à state == "READY" (max 180s, interval 2.5s)
while deployment["readyState"] not in {"READY", "ERROR"}:
    time.sleep(VERCEL_POLL_INTERVAL_SECONDS)
    deployment = httpx.get(f"{VERCEL_API_BASE}/v13/deployments/{dep_id}")

return {
    "deployment_id": dep_id,
    "full_url": f"https://{dep['url']}",
    "project_name": payload["name"],
    "state": "READY",
    "elapsed_seconds": elapsed
}
```

### 4.10 Persistance de session

**Fichier :** `tools/website_builder/website_project_persistence.py`

L'état complet du projet est sauvegardé dans `backend-api` à chaque étape clé :

| Champ | Contenu | Sauvegardé après |
|-------|---------|------------------|
| `description_json` | Architecture + contenu JSON | Phase 2A+2B |
| `approved` | Boolean | Approbation utilisateur |
| `current_html` | HTML complet courant | Phase 3, révisions, éditions |
| `current_version` | Entier incrémental | Chaque modification HTML |
| `status` | `"idle"` / `"generated"` / `"deployed"` | Changement de phase |
| `last_deployment_url` | URL Vercel | Phase 5 |
| `last_deployment_id` | ID déploiement Vercel | Phase 5 |
| `conversation_json` | Historique messages chat | Chaque message |

Au rechargement de la page, `bootstrapFromPersistence()` restaure l'état exact en moins de 2 requêtes HTTP, évitant toute re-génération coûteuse.

---

## Récapitulatif

| Aspect | Valeur |
|--------|--------|
| **Modèles utilisés** | `gpt-oss-120b` (phases 2+4) + `z-ai/glm-5.1` (phase 3) |
| **Fournisseur** | NVIDIA NIM |
| **Streaming** | SSE (Server-Sent Events) avec événements typés |
| **Déploiement cible** | Vercel (HTML statique) |
| **Temps génération typique** | 30–90 s (selon longueur HTML) |
| **Temps déploiement** | 10–30 s (polling Vercel jusqu'à READY) |
| **Persistance** | PostgreSQL via backend-api |
| **Frontend** | React + Tailwind CSS (split view chat/preview) |
| **Phases** | 5 phases : Contexte → Concept → Approbation → HTML → Déploiement |

---

*Document généré le 14 mai 2026 — Projet Brand AI (PFE)*
