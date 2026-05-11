# BrandAI — Plateforme Multi-Agents IA pour la Création de Marques

> *De l'idée à la marque déployée en ligne, orchestrée par un pipeline d'agents IA.*

BrandAI est une plateforme automatisée qui permet aux entrepreneurs de transformer une simple idée
de startup en **identité de marque complète** grâce à un pipeline multi-agents IA. À partir d'une
description en langage naturel, BrandAI génère successivement :

- **Clarification de l'idée** (validation, garde-fous de sécurité, questions de clarification)
- **Analyse de marché** (taille, concurrents, voix client, tendances, risques, stratégie)
- **Plan marketing** (positionnement, canaux, propositions de valeur)
- **Identité de marque** (nom, slogan, palette, logo généré par IA)
- **Génération de contenu social** (posts adaptés à Facebook / Instagram / LinkedIn, image incluse)
- **Site vitrine** (HTML/Tailwind/JS auto-généré + déploiement Vercel)
- **Optimiseur réseaux sociaux** (KPIs ETL + recommandations IA)

---

## Table des Matières

1. [Aperçu et Objectifs](#1-aperçu-et-objectifs)
2. [Architecture Globale](#2-architecture-globale)
3. [Stack Technologique](#3-stack-technologique)
4. [Structure du Repository](#4-structure-du-repository)
5. [Backend API — `backend-api`](#5-backend-api--backend-api)
6. [Backend IA — `backend-ai`](#6-backend-ia--backend-ai)
7. [Frontend — `frontend`](#7-frontend--frontend)
8. [Modèle de Données et Migrations](#8-modèle-de-données-et-migrations)
9. [Authentification et Sécurité](#9-authentification-et-sécurité)
10. [Pipeline Multi-Agents IA](#10-pipeline-multi-agents-ia)
11. [Pipeline ETL Réseaux Sociaux](#11-pipeline-etl-réseaux-sociaux)
12. [Intégrations Externes](#12-intégrations-externes)
13. [Observabilité et Logging](#13-observabilité-et-logging)
14. [Installation et Démarrage Local](#14-installation-et-démarrage-local)
15. [Variables d'Environnement](#15-variables-denvironnement)
16. [Commandes de Build, Run et Déploiement](#16-commandes-de-build-run-et-déploiement)
17. [Workflows de Bout en Bout](#17-workflows-de-bout-en-bout)
18. [Scalabilité, Performance et Maintenabilité](#18-scalabilité-performance-et-maintenabilité)
19. [Limitations Connues et Améliorations Futures](#19-limitations-connues-et-améliorations-futures)

---

## 1. Aperçu et Objectifs

### Problématique
Un entrepreneur en phase d'idéation doit **simultanément** valider sa proposition de valeur,
analyser son marché, construire une identité visuelle, produire du contenu et publier en ligne.
Chacune de ces tâches nécessite des compétences distinctes (stratégie, design, copywriting, dev web)
et des outils séparés.

### Solution
BrandAI orchestre tout ce parcours derrière une **interface unique** :
- L'utilisateur soumet son idée en français/anglais ;
- Le pipeline IA exécute en chaîne plusieurs agents spécialisés (LangChain / LangGraph) ;
- Chaque étape produit un artefact persistant et révisable (ex. brand kit, posts, site HTML) ;
- L'utilisateur peut publier directement sur les réseaux sociaux et déployer son site en un clic.

### Objectifs techniques
- **Modularité** : chaque agent est isolé, observable et remplaçable indépendamment.
- **Résilience** : rotation multi-clés (Groq, NVIDIA NIM, HF), retry exponentiel, garde-fous (Llama Guard).
- **Streaming temps réel** : SSE pour les phases longues (génération de site, ETL).
- **Persistance forte** : PostgreSQL + Alembic, snapshots immuables des publications planifiées.

---

## 2. Architecture Globale

BrandAI suit une architecture **trois services** déployables indépendamment :

```mermaid
flowchart LR
    subgraph Client["Frontend — React 19 + Vite"]
        UI[Pages & Pipeline UI]
        SSEHook[hooks SSE & Auth Context]
    end

    subgraph API["backend-api — FastAPI (REST)"]
        Auth[Auth & JWT/OAuth]
        Persistence[(SQLAlchemy ORM)]
        Worker[Worker: scheduled_publisher]
        Crypto[Crypto: tokens sociaux]
    end

    subgraph AI["backend-ai — FastAPI (Agents IA)"]
        Clarifier[Clarifier]
        Market[Market Analysis Graph]
        Brand[Branding Agents]
        Content[Content ReAct Agent]
        Website[Website Builder]
        Optimizer[Social Optimizer]
        ETL[Social ETL Pipeline]
    end

    subgraph Data["PostgreSQL"]
        Tables[(users, ideas, brand_kit,<br/>generated_contents,<br/>scheduled_publications,<br/>social_etl_*, …)]
    end

    subgraph External["Services tiers"]
        NVIDIA[NVIDIA NIM<br/>gpt-oss-120b]
        Groq[Groq LLaMA / Llama-Guard]
        HF[HuggingFace + Pollinations<br/>Image Gen]
        Cloudinary[Cloudinary CDN]
        Vercel[Vercel Deploy]
        Meta[Meta Graph API]
        LI[LinkedIn API]
        Apify[Apify LinkedIn Actor]
        Google[Google OAuth]
    end

    UI --> Auth
    UI --> Clarifier
    UI --> Market
    UI --> Brand
    UI --> Content
    UI --> Website
    UI --> Optimizer
    SSEHook -. SSE .-> AI

    Auth --> Persistence
    Persistence --> Tables
    Worker --> Tables
    Worker --> Meta
    Worker --> LI

    Clarifier --> NVIDIA
    Clarifier --> Groq
    Brand --> NVIDIA
    Brand --> HF
    Brand --> Cloudinary
    Content --> NVIDIA
    Content --> HF
    Content --> Cloudinary
    Website --> NVIDIA
    Website --> Vercel
    ETL --> Meta
    ETL --> Apify
    ETL --> Tables
    Optimizer --> Tables
    Optimizer --> NVIDIA

    AI -.-> Persistence
    AI -. JWT .-> Auth
    Auth --> Google
```

### Séparation des responsabilités

| Service        | Rôle principal                                           | Port défaut |
|----------------|----------------------------------------------------------|-------------|
| `frontend`     | UI React, gestion de session, orchestration UX du pipeline | 5173       |
| `backend-api`  | Authentification, CRUD persistant, OAuth social, worker de publication | 8000       |
| `backend-ai`   | Exécution des agents IA, génération de contenu, ETL social, RAG-like flows | 8001       |

Le **backend-ai** ne gère pas l'authentification : il **valide les JWT** émis par le backend-api
et appelle ce dernier en HTTP pour persister les artefacts (brand kit, contenu, site).

---

## 3. Stack Technologique

### Backend (Python 3.11+)
| Domaine                | Technologies                                                     |
|------------------------|------------------------------------------------------------------|
| Framework Web          | FastAPI 0.135, Uvicorn 0.41, Starlette 0.52                       |
| ORM / Migrations       | SQLAlchemy 2.0, Alembic 1.18, psycopg2-binary, asyncpg            |
| Validation             | Pydantic 2.12, pydantic-settings                                  |
| Auth                   | python-jose (JWT), passlib + bcrypt, Authlib (OAuth Google/LinkedIn) |
| LLM Orchestration      | LangChain 1.2, LangGraph 1.1, langgraph-prebuilt (`create_react_agent`) |
| LLM Providers          | NVIDIA NIM (gpt-oss-120b), Groq (LLaMA + Llama-Guard), Azure OpenAI, Google GenAI |
| Image Gen              | HuggingFace InferenceClient, Pollinations (fallback)              |
| CDN / Stockage médias  | Cloudinary                                                        |
| Observabilité          | structlog, OpenTelemetry SDK + OTLP exporter, LangSmith            |
| Background tasks       | asyncio + thread dédié (`scheduled_publisher`)                    |
| Scraping / SERP        | Tavily, SerpAPI, BeautifulSoup, lxml, Apify                       |
| Streaming SSE          | sse-starlette                                                     |

### Frontend (Node 20+)
| Domaine        | Technologies                              |
|----------------|-------------------------------------------|
| Framework      | React 19, react-router-dom v7             |
| Build tool     | Vite 8, @vitejs/plugin-react              |
| Styling        | TailwindCSS 3.4, PostCSS, Autoprefixer    |
| Notifications  | react-toastify                            |
| Icônes         | react-icons                               |
| Lint           | ESLint 9, eslint-plugin-react-hooks       |

### Infrastructure
- **PostgreSQL** (toute version compatible asyncpg / psycopg2)
- **Vercel** pour le déploiement des sites générés
- **Cloudinary** pour l'hébergement des images générées
- **Vercel** (frontend) — autorisations CORS via regex `https://.*\.vercel\.app`

---

## 4. Structure du Repository

```
Brand AI/
├── backend-ai/                  # Service IA — agents, pipelines, ETL
│   ├── app/
│   │   ├── main.py              # Point d'entrée FastAPI
│   │   ├── routes/              # Routes HTTP par domaine (clarifier, branding, …)
│   │   └── services/            # Branding service, step runner, persistence
│   ├── agents/                  # Agents IA (BaseAgent + spécialisations)
│   │   ├── base_agent.py
│   │   ├── clarifier/
│   │   ├── market_analysis/
│   │   ├── branding/            # name, slogan, palette, logo
│   │   ├── content_generation/  # ReAct + weekly plan
│   │   ├── marketing/
│   │   ├── social_optimizer/
│   │   └── website_builder/
│   ├── tools/                   # Outils LangChain (@tool) appelés par les agents
│   │   ├── branding/
│   │   ├── content_generation/
│   │   ├── market_analysis/     # Tavily, SerpAPI, news, scraping
│   │   ├── social_publishing/   # Meta, LinkedIn, OAuth state, callback proxy
│   │   ├── social_optimizer/
│   │   └── website_builder/     # architecture/coder/refinement/Vercel deploy
│   ├── pipeline/                # LangGraph state graphs (market_graph, …)
│   ├── llm/                     # llm_factory + llm_rotator (multi-clés)
│   ├── prompts/                 # Prompts système / utilisateur par agent
│   ├── guardrails/              # Llama Guard, refus
│   ├── shared/                  # Validateurs partagés (branding)
│   ├── social_etl/              # Pipeline ETL : extraction / normalisation / KPIs / load
│   ├── observability/           # logging.py (structlog)
│   ├── config/                  # YAML + settings (clés, Azure, LangSmith)
│   └── requirements.txt
│
├── backend-api/                 # API persistante — Auth + CRUD
│   ├── app/
│   │   ├── main.py              # FastAPI + CORS + worker
│   │   ├── api/routes/          # auth, ideas, branding_results, optimizer, …
│   │   ├── api/deps.py          # get_current_user (JWT)
│   │   ├── core/                # config, database, security, oauth, social_token_crypto
│   │   ├── models/              # SQLAlchemy ORM (users, ideas, brand_kit, …)
│   │   ├── schemas/             # Pydantic IO schemas
│   │   ├── services/            # Logique métier (auth_service, social_etl_runner, …)
│   │   ├── workers/             # scheduled_publisher (thread)
│   │   ├── agents/tools/        # Helpers pour social_media_optimizer
│   │   └── observability/
│   ├── alembic/                 # Migrations versionnées (~24 révisions)
│   ├── alembic.ini
│   └── requirements.txt
│
├── frontend/                    # SPA React
│   ├── src/
│   │   ├── App.jsx → app/App.jsx (BrowserRouter + AuthProvider)
│   │   ├── app/layout/          # PipelineLayout (sidebar agents)
│   │   ├── pages/               # Landing, Login, Dashboard, IdeaPage, …
│   │   ├── agents/              # Pages par agent (clarifier, market, brand, …)
│   │   ├── pipeline/components/ # Bandeau de progression, étapes XAI
│   │   ├── components/          # NotificationBell, ProtectedRoute, ui/
│   │   ├── context/             # AuthContext, PipelineContext
│   │   ├── hooks/               # useAuth, useNotificationsSSE
│   │   └── services/            # *Api.js (fetch wrappers)
│   ├── package.json
│   ├── vite.config.js           # alias "@" → ./src
│   └── tailwind.config.js
│
└── README.md                    # Ce document
```

---

## 5. Backend API — `backend-api`

Service d'**ancrage métier** : authentification, persistance, workflows transactionnels.
Tous les artefacts produits par les agents IA sont stockés ici via un appel HTTP authentifié JWT.

### Points d'entrée principaux ([app/main.py](backend-api/app/main.py))

- Création de l'instance FastAPI + `SessionMiddleware` (Authlib) + `CORSMiddleware`.
- Import explicite des modèles SQLAlchemy pour enregistrer le metadata.
- `Base.metadata.create_all(...)` au démarrage *(complément à Alembic en dev)*.
- Démarrage d'un **thread dédié** exécutant `run_publisher_loop()` — boucle d'auto-publication.

### Routers exposés

| Préfixe                                                     | Fichier                       | Rôle                                              |
|-------------------------------------------------------------|-------------------------------|---------------------------------------------------|
| `/api/auth/*`                                               | `routes/auth.py`              | register/login/me + OAuth Google                  |
| `/api/ideas/*`                                              | `routes/ideas.py`             | CRUD idées + clarifier persist + pipeline progress |
| `/api/ideas/{id}/market-analysis`                           | `routes/market_analysis.py`   | Read/write résultats analyse marché               |
| `/api/ideas/{id}/marketing-plans`                           | `routes/marketing_plans.py`   | Read/write plan marketing                         |
| `/api/ideas/{id}/branding/*`                                | `routes/branding_results.py`  | Brand kit (naming/slogan/palette/logo)            |
| `/api/ideas/{id}/generated-contents`                        | `routes/idea_generated_contents.py` | Posts générés                              |
| `/api/ideas/{id}/scheduled-publications`                    | `routes/idea_scheduled_publications.py` | File de publication                  |
| `/api/ideas/{id}/social-connections`                        | `routes/social_connections.py` | Tokens Meta/LinkedIn (chiffrés)                  |
| `/api/ideas/{id}/optimizer/*`                               | `routes/optimizer.py`         | KPIs + recommandations + déclenchement ETL        |
| `/api/notifications/*`                                      | `routes/notifications.py`     | SSE notifications (push UI)                       |
| `/api/ideas/{id}/website-projects`                          | `routes/website_projects.py`  | Brouillon, HTML, métadonnées Vercel               |

### Couche Services
Chaque router délègue à un service (`services/*_service.py`) qui encapsule la logique métier et
les transactions SQLAlchemy. Exemple : `scheduled_publication_service.create(...)` vérifie la
connexion sociale, snapshot le contenu et planifie l'envoi.

### Worker de publication
[`app/workers/scheduled_publisher.py`](backend-api/app/workers/scheduled_publisher.py) tourne dans
un **thread asyncio dédié** (poll = 30 s) :
1. Récupère les `ScheduledPublication` au statut `scheduled` arrivés à échéance ;
2. Déchiffre les tokens sociaux via `social_token_crypto` ;
3. Appelle `platform_publisher.publish_to_platform(...)` (Meta Graph / LinkedIn UGC) ;
4. Met à jour le statut (`published` / `failed`), incrémente `attempt_count`, crée une
   `Notification` consommable côté frontend par SSE.

---

## 6. Backend IA — `backend-ai`

Service spécialisé dans l'**exécution des agents IA**. N'a pas de base utilisateur : reçoit le
JWT du frontend, l'utilise pour appeler `backend-api` (lecture du brief, persistance des résultats).

### Hiérarchie des agents

```mermaid
classDiagram
    class BaseAgent {
        +agent_name
        +temperature
        +llm_model
        +llm_max_tokens
        +llm_rotator: LLMRotator
        +_call_llm(system, user)
        +_call_nvidia_direct(...)  // rotation 4 clés + 3 cycles
        +_call_langchain(...)      // fallback Groq
        +_parse_json(raw)
        +run(state)*
    }

    class ClarifierAgent
    class KeywordExtractor
    class MarketSizingAgent
    class CompetitorAgent
    class VOCAgent
    class TrendsRisksAgent
    class StrategyAnalysisAgent
    class MarketingAgent
    class NameAgent
    class SloganAgent
    class PaletteAgent
    class LogoAgent
    class ContentReActAgent
    class WeeklyPlanAgent
    class SocialOptimizerRecommendationAgent
    class WebsiteBuilderOrchestrator

    BaseAgent <|-- ClarifierAgent
    BaseAgent <|-- KeywordExtractor
    BaseAgent <|-- MarketSizingAgent
    BaseAgent <|-- CompetitorAgent
    BaseAgent <|-- VOCAgent
    BaseAgent <|-- TrendsRisksAgent
    BaseAgent <|-- StrategyAnalysisAgent
    BaseAgent <|-- MarketingAgent
    BaseAgent <|-- NameAgent
    BaseAgent <|-- SloganAgent
    BaseAgent <|-- PaletteAgent
    BaseAgent <|-- LogoAgent
    BaseAgent <|-- ContentReActAgent
    BaseAgent <|-- WeeklyPlanAgent
    BaseAgent <|-- SocialOptimizerRecommendationAgent
    BaseAgent <|-- WebsiteBuilderOrchestrator
```

### `BaseAgent` ([agents/base_agent.py](backend-ai/agents/base_agent.py))

Abstraction commune qui implémente :

- **Routage LLM intelligent** :
  - `openai/gpt-oss-120b` → **NVIDIA NIM uniquement** (rotation 4 clés, 3 cycles, retry sur 429).
  - Autres modèles → **LangChain + Groq** via `LLMRotator`.
- **Gestion de la fenêtre** : timeout HTTP NVIDIA configurable (`NVIDIA_HTTP_TIMEOUT_S`), output
  capé à 65 536 tokens.
- **Parser JSON tolérant** : élimine les fences markdown, extrait le premier bloc `{}` équilibré.
- **`PipelineState`** : objet d'état mutable partagé entre les nœuds d'un graphe LangGraph
  (clarified_idea, market_analysis, brand_identity, content, errors, …).

### `LLMRotator` ([llm/llm_rotator.py](backend-ai/llm/llm_rotator.py))
Rotation cyclique entre N clés Groq pour absorber les rate-limits (40 RPM par clé NVIDIA, quotas
Groq). Constructors helper : `groq_only()`, `groq_gpt_only()`, `groq_model(...)`.

### Routes IA ([app/main.py](backend-ai/app/main.py))

| Route                                  | Agent / Pipeline                              |
|----------------------------------------|-----------------------------------------------|
| `POST /api/ai/clarifier/*`             | `ClarifierAgent`                              |
| `POST /api/ai/market-analysis/*`       | `MarketGraph` (LangGraph)                     |
| `POST /api/ai/market-strategy/*`       | `MarketStrategyGraph`                         |
| `POST /api/ai/branding/{naming\|slogan\|palette\|logo}` | Agents branding individuels       |
| `POST /api/ai/content-generation/*`    | `ContentReActAgent` (LangGraph ReAct)         |
| `POST /api/ai/content-weekly-plan/*`   | `WeeklyPlanAgent`                             |
| `POST /api/ai/social-publish/*`        | `social_publishing` tools (Meta + LinkedIn)   |
| `POST /api/ai/social-optimizer/*`      | `SocialOptimizerRecommendationAgent`          |
| `POST /api/ai/website/*`               | `WebsiteBuilderOrchestrator` (SSE)            |

Un proxy callback LinkedIn local est lancé via `lifespan` pour intercepter le code OAuth
(`tools/social_publishing/linkedin_callback_proxy.py`).

---

## 7. Frontend — `frontend`

SPA React 19 servie par Vite. Le routeur ([src/app/App.jsx](frontend/src/app/App.jsx)) découpe
l'application en deux espaces :

- **Public** : `/`, `/login`, `/register`, `/auth/callback`, `/privacy` (gardés par `<PublicRoute>`).
- **Protégé** : `/dashboard`, `/ideas/*` (gardés par `<ProtectedRoute>` qui vérifie le contexte Auth).

### Pipeline UI

Chaque idée lance un sous-routeur sous `/ideas/:id/*` rendu par `<PipelineLayout>` :

```
/ideas/:id/clarifier
/ideas/:id/market
/ideas/:id/marketing
/ideas/:id/brand
/ideas/:id/content/{connect,publish,schedule}
/ideas/:id/website
/ideas/:id/optimizer
```

Chaque page d'agent est isolée sous `src/agents/<agent>/pages/`, avec ses propres hooks et
composants. La progression est partagée via `PipelineContext`.

### Communication avec les backends

- `src/services/*Api.js` : wrappers `fetch()` avec gestion homogène des erreurs (`getErrorMessage`).
- `VITE_API_URL` (par défaut `http://localhost:8000/api`) pour le backend-api.
- Les flux IA (Website Builder, ETL) utilisent le **streaming SSE** consommé via `EventSource` /
  hook custom (ex. `useNotificationsSSE`).

### Build / Dev
```bash
npm run dev      # Vite dev server
npm run build    # Bundle de production dans dist/
npm run preview  # Preview du build
npm run lint     # ESLint
```

---

## 8. Modèle de Données et Migrations

### Schéma logique (PostgreSQL)

```mermaid
erDiagram
    USERS ||--o{ IDEAS : owns
    IDEAS ||--o{ MARKET_ANALYSIS_RESULTS : has
    IDEAS ||--o{ MARKETING_PLANS : has
    IDEAS ||--o{ BRAND_IDENTITIES : has
    IDEAS ||--o| NAMING_RESULTS : has
    IDEAS ||--o| SLOGAN_RESULTS : has
    IDEAS ||--o| PALETTE_RESULTS : has
    IDEAS ||--o| LOGO_RESULTS : has
    IDEAS ||--o| BRAND_KITS : has
    IDEAS ||--o{ GENERATED_CONTENTS : has
    IDEAS ||--o{ SCHEDULED_PUBLICATIONS : has
    IDEAS ||--o{ USER_SOCIAL_CONNECTIONS : has
    IDEAS ||--o| WEBSITE_PROJECTS : has
    USERS ||--o{ NOTIFICATIONS : receives
    USER_SOCIAL_CONNECTIONS ||--o{ SOCIAL_ETL_POSTS : feeds
    SOCIAL_ETL_POSTS ||--o{ SOCIAL_ETL_DAILY_INSIGHTS : aggregates
    GENERATED_CONTENTS ||--o{ SCHEDULED_PUBLICATIONS : snapshot
```

### Tables principales (modèles SQLAlchemy)

| Table                       | Modèle                | Rôle                                                      |
|-----------------------------|-----------------------|-----------------------------------------------------------|
| `users`                     | `User`                | Compte (email + bcrypt OR google_id), avatar              |
| `ideas`                     | `Idea`                | Brief utilisateur + résultats Clarifier + `pipeline_progress` JSON |
| `market_analysis_results`   | `MarketAnalysisResult`| Sortie complète du graphe d'analyse marché                |
| `marketing_plans`           | `MarketingPlan`       | Stratégie marketing                                       |
| `brand_identities` + `*_results` + `brand_kits` | … | Naming / slogan / palette / logo + agrégat brand_kit     |
| `generated_contents`        | `GeneratedContent`    | Posts (caption + image_url Cloudinary, plateforme, brief) |
| `scheduled_publications`    | `ScheduledPublication`| File d'envoi (snapshot caption + image, status, retries)  |
| `user_social_connections`   | `SocialConnection`    | Tokens Meta/LinkedIn **chiffrés** (Fernet)               |
| `notifications`             | `Notification`        | Push events (publication réussie/échouée, rapport ETL)    |
| `website_projects`          | `WebsiteProject`      | Description JSON, HTML courant, état Vercel               |
| `social_etl_*`              | (asyncpg)             | `posts`, `daily_insights`, `kpis_30d`, `sync_logs`        |

### Migrations Alembic
24 révisions versionnées dans [`backend-api/alembic/versions/`](backend-api/alembic/versions/).
Exemples :
- `395e0e99d3f6_create_users_table`
- `c3d4e5f6g7h8_add_pipeline_progress_to_ideas`
- `j2k3l4m5n6o7_create_branding_results_and_brand_kits`
- `m5n6o7p8q9r0_create_scheduled_publications`
- `t1u2v3w4x5y6_social_connections_table_refactor`
- `u2v3w4x5y6z7_create_social_etl_tables`

```bash
# Appliquer toutes les migrations
cd backend-api
alembic upgrade head

# Créer une nouvelle révision
alembic revision -m "describe_change" --autogenerate
```

---

## 9. Authentification et Sécurité

### Flux JWT classique
1. `POST /api/auth/register` ou `/login` → token JWT signé HS256 (`SECRET_KEY`, exp 24 h).
2. Le frontend stocke le token (localStorage) ; le hook `useAuth` l'injecte dans chaque appel.
3. La dépendance `get_current_user` ([api/deps.py](backend-api/app/api/deps.py)) décode le token
   et charge l'utilisateur courant.
4. Le **backend-ai accepte le même JWT** : il l'utilise pour rappeler `backend-api` lorsqu'il
   doit lire ou écrire un brief / brand kit.

### OAuth Google
Implémenté avec **Authlib** ([core/oauth.py](backend-api/app/core/oauth.py)) :
- `GET /api/auth/google` → `authorize_redirect`.
- `GET /api/auth/google/callback` → échange du code, lookup ou création utilisateur (lien par
  `google_id` puis fallback par email), génération du JWT et redirection vers
  `FRONTEND_CALLBACK_URL?token=…`.

### OAuth réseaux sociaux
- **Meta (Facebook/Instagram Business)** : flow OAuth standard + appel Graph API pour récupérer
  les pages disponibles, persistance dans `user_social_connections`.
- **LinkedIn** : `tools/social_publishing/linkedin_client.py`. Comme LinkedIn impose un
  `redirect_uri` HTTPS, le backend-ai démarre un **proxy local** (`linkedin_callback_proxy.py`)
  pendant l'OAuth pour réceptionner le callback en dev.

### Chiffrement des tokens sociaux
[`core/social_token_crypto.py`](backend-api/app/core/social_token_crypto.py) chiffre les
`access_token` et `refresh_token` (Fernet) avant insertion en base. Le worker de publication
appelle `get_decrypted_tokens_for_publish(...)` qui retourne le token clair en mémoire uniquement.

### Garde-fous IA
[`guardrails/safety_checks.py`](backend-ai/guardrails/safety_checks.py) appelle
`meta/llama-guard-4-12b` via NVIDIA NIM avant toute exécution sensible (clarifier).
Catégories de refus : `fraud`, `illegal`, `harmful`, `default`.

---

## 10. Pipeline Multi-Agents IA

### Vue d'ensemble du pipeline complet

```mermaid
sequenceDiagram
    actor U as Utilisateur
    participant F as Frontend
    participant API as backend-api
    participant AI as backend-ai
    participant DB as PostgreSQL
    participant LLM as NVIDIA NIM / Groq

    U->>F: Soumet une idée
    F->>API: POST /ideas
    API->>DB: INSERT idea (status=pending)

    F->>AI: POST /clarifier (JWT)
    AI->>LLM: Llama-Guard (safety) + Clarifier prompt
    AI-->>F: questions / score / pitch
    F->>API: PATCH /ideas/{id}/clarifier-result

    F->>AI: POST /market-analysis
    AI->>LLM: KeywordExtractor → 5 sub-agents (LangGraph)
    AI->>API: PATCH market_analysis
    AI-->>F: rapport JSON

    F->>AI: POST /marketing-plan
    AI->>API: PATCH marketing_plan

    F->>AI: POST /branding (naming → slogan → palette → logo)
    AI->>LLM: gpt-oss-120b
    AI->>HF: image gen logo
    AI->>Cloudinary: upload logo
    AI->>API: PATCH brand_kit

    F->>AI: POST /content-weekly-plan
    AI->>LLM: weekly plan
    F->>AI: POST /content-generation (par item)
    AI->>LLM: ReAct (5 outils)
    AI->>HF: image post
    AI->>Cloudinary: upload image
    AI->>API: POST generated_contents

    F->>API: POST scheduled-publications
    Note over API: Worker thread poll toutes les 30s
    API->>Meta/LinkedIn: publish
    API->>DB: status=published

    F->>AI: SSE /website/description/stream
    AI->>LLM: architecture + content
    F->>AI: SSE /website/generate/stream
    AI->>LLM: HTML/Tailwind/JS
    AI->>Vercel: deploy
    AI->>API: PATCH website_project
```

### Agent Clarifier
Vérifie la sécurité (Llama-Guard), détecte le baragouin, génère des questions complémentaires si
le score de clarté est faible, produit un pitch court et un statut (`accepted`, `needs_clarification`,
`refused`).

### Sous-pipeline Analyse de Marché (LangGraph)
[`pipeline/market_graph.py`](backend-ai/pipeline/market_graph.py) construit un `StateGraph` :

```
START → keyword_extractor → market_sizing → competitor → voc → trends_risks → strategy_analysis → save_results → END
```

Chaque nœud invoque un sous-agent dédié (`MarketSizingAgent`, `CompetitorAgent`, …) qui utilise
des outils externes : **Tavily** (search), **SerpAPI**, **scrape_tool** (BeautifulSoup), **news_tool**.

### Agents Branding
- `name_agent.py` → propositions de noms + vérif domaine/originalité.
- `slogan_agent.py` → variations courtes / longues.
- `palette_agent.py` → palette HEX + reasoning.
- `logo_agent.py` → **agent ReAct LangGraph** : `make_draft_logo_prompt_tool` → `make_render_logo_image_tool`
  (HF puis Pollinations en fallback) → `verifier_originalite_logo_bytes` (Google Cloud Vision).

### Agent ContentGeneration (ReAct)
[`agents/content_generation/content_react_agent.py`](backend-ai/agents/content_generation/content_react_agent.py)
utilise `langgraph.prebuilt.create_react_agent` avec **5 outils** :
1. `merge_context` — récupère le brief et le brand kit via `backend-api` ;
2. `get_platform_spec` — limites caractères / ratios image (`platform_specs.py`) ;
3. `draft_post` — légende avec `ContentLLMRunner` ;
4. `build_image_prompt` — JSON `image_prompt` + `negative_prompt` ;
5. `image_client` — HF → Pollinations → upload Cloudinary → URL publique.

L'orchestrateur LLM (NVIDIA NIM, `gpt-oss-120b`) enchaîne les tool calls. Trace `react_trace.py`
imprimée en terminal pour debug + LangSmith.

### Agent Website Builder
Pipeline en **5 phases** orchestrées par [`WebsiteBuilderOrchestrator`](backend-ai/agents/website_builder/orchestrator.py)
et streamées en SSE :

| Phase | Endpoint                                | Action                                                      |
|-------|-----------------------------------------|-------------------------------------------------------------|
| 1     | `GET /website/context`                  | Récupère brand kit + idée                                   |
| 2     | `POST /website/description/stream`      | Architecture (sections, nav, animations) + contenu textuel  |
| 2.5   | `POST /website/description/refine/stream` | Affinage par chat                                          |
| 3     | `POST /website/generate/stream`         | Génération HTML/Tailwind/JS + QA validation + auto-fix      |
| 4     | `POST /website/revise/stream`           | Modifications chirurgicales par instruction                 |
| 5     | `POST /website/deploy`                  | Déploiement Vercel (API REST) + persistance URL             |

La QA (`validator_tool.py`) vérifie que le slogan et le nom de marque sont présents, que la
navigation est cohérente (ancres `#id` valides), que le HTML est responsive (meta viewport,
breakpoints, nav mobile). En cas d'échec, un cycle de réparation automatique est déclenché.

### Agent Social Optimizer
[`agents/social_optimizer/recommendation_agent.py`](backend-ai/agents/social_optimizer/recommendation_agent.py)
récupère le contexte projet (`get_project_context`), les KPIs ETL 30 jours
(`get_current_kpis` → `/api/ideas/{id}/optimizer/stats`), puis appelle NVIDIA NIM avec
`response_format={"type":"json_object"}` pour produire un JSON normalisé :

```json
{
  "platform": "instagram",
  "summary": "…",
  "recommendations": [
    {"id": 1, "title": "…", "description": "…", "actions": ["…"], "priority": "high"}
  ]
}
```

Cache : la dernière recommandation par `(idea_id, platform)` est servie sauf si `force=true`.

---

## 11. Pipeline ETL Réseaux Sociaux

[`backend-ai/social_etl/pipeline.py`](backend-ai/social_etl/pipeline.py) orchestre l'extraction
des métriques sociales pour alimenter l'Optimizer.

### Étapes par compte
```mermaid
flowchart LR
    A[log_sync started] --> B{platform?}
    B -->|facebook| C1[extract_facebook<br/>Meta Graph]
    B -->|instagram| C2[extract_instagram<br/>Meta Graph]
    B -->|linkedin| C3[extract_linkedin<br/>Apify Actor]
    C1 --> D[normalize_facebook]
    C2 --> D2[normalize_instagram]
    C3 --> D3[normalize_linkedin]
    D --> E[upsert_posts]
    D2 --> E
    D3 --> E
    E --> F[upsert_daily_insights]
    F --> G[compute_kpis_30d]
    G --> H[log_sync success]
```

- **Extraction** : Meta Graph API (`facebook_extractor`, `instagram_extractor`) ; Apify LinkedIn
  Actor pour les pages LinkedIn (token + actor_id requis).
- **Normalisation** : transforme les payloads tiers en schéma uniforme `{posts[], followers_count,
  reach, impressions, post_engagements}` (`normalize_*`).
- **Chargement** : `upsert_posts`, `upsert_daily_insights` (asyncpg, batch).
- **KPIs** : agrégats 30 jours par plateforme (`kpis/*`).
- **Audit** : table `social_etl_sync_logs` avec `status`, `posts_fetched`, `error_message`,
  durée d'exécution.

### Modes d'exécution
- **Direct (CLI)** : `python -m social_etl.pipeline --config config.json`.
- **Async dict** : `run_pipeline_async(cfg)` (utilisé par `backend-api/services/social_etl_runner.py`).
- **SSE** : `run_pipeline_events(cfg)` émet `started`, `platform_start/done/error`, `complete`.

---

## 12. Intégrations Externes

| Service             | Usage                                              | Variables clés                                    |
|---------------------|----------------------------------------------------|---------------------------------------------------|
| **NVIDIA NIM**      | LLM principal (`gpt-oss-120b`) + Llama-Guard       | `NVIDIA_API_KEY_1..4`, `NVIDIA_HTTP_TIMEOUT_S`    |
| **Groq**            | LLaMA / fallback rotation                          | `GROQ_API_KEY`, `GROQ_API_KEY_2`, `GROQ_API_KEY_3`|
| **Azure OpenAI**    | Logo agent, alternatives                           | `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |
| **Google GenAI**    | Helpers / vision                                   | `GEMINI_API_KEY*`                                 |
| **HuggingFace**     | Image gen logo + posts                             | `HF_TOKEN_1..N`, `HUGGINGFACE_API_KEY_*`         |
| **Pollinations**    | Fallback image gen                                 | `POLLINATIONS_API_KEY`                            |
| **Cloudinary**      | CDN images générées                                | `CONTENT_CLOUDINARY_*` / `CLOUDINARY_*`           |
| **Tavily / SerpAPI**| Recherche web pour Market Analysis                 | `TAVILY_API_KEY`, `SERPAPI_API_KEY`               |
| **Google Cloud Vision** | Vérification originalité logo                  | service-account JSON                              |
| **Meta Graph API**  | Publication FB/IG, ETL                             | tokens utilisateur (chiffrés en DB)               |
| **LinkedIn API**    | Publication UGC, OAuth                             | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI` |
| **Apify**           | Scraping LinkedIn pages                            | `APIFY_TOKEN`, `APIFY_LINKEDIN_ACTOR_ID`         |
| **Vercel**          | Déploiement sites générés                          | `VERCEL_TOKEN`, `VERCEL_PROJECT_PREFIX`          |
| **Google OAuth**    | SSO frontend                                       | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`       |
| **LangSmith**       | Traces IA                                          | `LANGCHAIN_API_KEY` (projet `brand-ai`)          |

---

## 13. Observabilité et Logging

- **structlog** + format texte coloré (`%(levelname)s [%(name)s] %(message)s`).
- Loggers nommés (`brandai.*`) configurés dans [`backend-ai/app/main.py`](backend-ai/app/main.py)
  pour exposer le détail des agents (`brandai.logo_agent`, `brandai.content_react_agent`,
  `brandai.llm_rotator`, …).
- **OpenTelemetry SDK** + exporter OTLP/HTTP (proto-common 1.40) installés ; configuration via
  les variables `OTEL_EXPORTER_OTLP_*` standard.
- **LangSmith** : décorateurs `@traceable` sur l'orchestrateur Website Builder, l'agent ReAct
  Content, l'Optimizer (tags `social_optimizer`, `website_builder`, `tools`).
- **Sync logs ETL** : table `social_etl_sync_logs` (`status`, `error_message`, `posts_fetched`,
  durée).
- **react_trace.py** : impression console des cycles Thought/Action/Observation pour debug
  (désactivable par `CONTENT_AGENT_VERBOSE_TERMINAL=0`).

---

## 14. Installation et Démarrage Local

### Prérequis
- Python **3.11+**
- Node.js **20+** (pnpm/npm)
- PostgreSQL **14+** opérationnel et accessible
- Comptes / clés API : a minima NVIDIA (1 clé), Groq (1 clé), Cloudinary, Tavily

### 1. Cloner le repo
```bash
git clone <repo-url>
cd "Brand AI"
```

### 2. Configurer le `.env` racine
Créer un fichier `.env` à la racine (lu par les deux backends — voir [§15](#15-variables-denvironnement)).

### 3. Démarrer PostgreSQL et créer la base
```bash
createdb brandai
```

### 4. Backend API
```bash
cd backend-api
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
alembic upgrade head             # applique les migrations
uvicorn app.main:app --reload --port 8000
```

### 5. Backend AI
```bash
cd ../backend-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 6. Frontend
```bash
cd ../frontend
npm install
npm run dev                      # http://localhost:5173
```

### 7. Vérification
- API : `curl http://localhost:8000/health` → `{"status":"ok","app":"BrandAI API"}`
- AI :  `curl http://localhost:8001/health` → `{"status":"ok","service":"brandai-ai"}`
- Front : ouvrir `http://localhost:5173`

---

## 15. Variables d'Environnement

Fichier `.env` unique à la racine (consommé par les deux backends — `backend-ai` charge via
`python-dotenv` dans [`config/settings.py`](backend-ai/config/settings.py), `backend-api` via
`pydantic-settings`).

### Application
```env
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/brandai
SECRET_KEY=change-me-32-bytes
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
APP_ENV=development
FRONTEND_URL=http://localhost:5173
FRONTEND_CALLBACK_URL=http://localhost:5173/auth/callback
```

### Auth Google
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

### LLM Providers
```env
# NVIDIA NIM (rotation 4 clés conseillée)
NVIDIA_API_KEY_1=nvapi-...
NVIDIA_API_KEY_2=
NVIDIA_API_KEY_3=
NVIDIA_API_KEY_4=
NVIDIA_HTTP_TIMEOUT_S=600

# Groq
GROQ_API_KEY=gsk_...
GROQ_API_KEY_2=
GROQ_API_KEY_3=

# Azure OpenAI (logo agent)
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_LOGO_DEPLOYMENT=
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Gemini (optionnel)
GEMINI_API_KEY=
```

### Image Gen + CDN
```env
HF_TOKEN_1=hf_...
HF_TOKEN_2=
POLLINATIONS_API_KEY=
CONTENT_CLOUDINARY_CLOUD_NAME=
CONTENT_CLOUDINARY_API_KEY=
CONTENT_CLOUDINARY_API_SECRET=
```

### Outils Market Analysis
```env
TAVILY_API_KEY=
SERPAPI_API_KEY=
```

### Réseaux sociaux
```env
META_GRAPH_API_VERSION=v25.0
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_REDIRECT_URI=https://localhost:8443/linkedin/callback
APIFY_TOKEN=
APIFY_LINKEDIN_ACTOR_ID=
```

### Vercel + Observabilité
```env
VERCEL_TOKEN=
VERCEL_PROJECT_PREFIX=brandai
LANGCHAIN_API_KEY=ls__...
```

### Frontend
```env
# frontend/.env (préfixé VITE_ pour exposition)
VITE_API_URL=http://localhost:8000/api
VITE_AI_URL=http://localhost:8001/api/ai
```

---

## 16. Commandes de Build, Run et Déploiement

### Backend API
```bash
# Dev
uvicorn app.main:app --reload --port 8000

# Production (workers gunicorn)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Migrations
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "add_table_x"
```

### Backend AI
```bash
# Dev
uvicorn app.main:app --reload --port 8001

# ETL CLI
python -m social_etl.pipeline --config etl_config.json

# Clear cache LLM (si besoin)
python clear_cache.py
```

### Frontend
```bash
npm run dev      # dev server
npm run build    # bundle prod -> dist/
npm run preview  # preview du build
npm run lint
```

### Déploiement
- **Frontend** : Vercel ou Netlify (`npm run build`, déploiement statique de `dist/`).
- **Backend API + AI** : conteneurs Docker (Dockerfile à ajouter), Render/Railway/Fly.io ou
  serveur dédié derrière un reverse proxy (Nginx) avec TLS.
- **PostgreSQL** : managé (Neon, Supabase, RDS) recommandé pour la production.

---

## 17. Workflows de Bout en Bout

### A. Création d'une marque complète (parcours utilisateur)
1. **Inscription** → `POST /api/auth/register` → JWT.
2. **Soumission de l'idée** → `POST /api/ideas` (status `pending`).
3. **Clarifier** : si nécessaire, l'utilisateur répond aux questions ; le pipeline mémorise
   `clarity_*` dans `ideas`.
4. **Market Analysis** : déclenche le `MarketGraph`, écrit dans `market_analysis_results`.
5. **Marketing Plan** : `MarketingAgent` consomme l'idée + l'analyse.
6. **Branding** : 4 sous-étapes séquentielles (naming → slogan → palette → logo). Brand Kit
   agrégé dans `brand_kits`.
7. **Content** : `WeeklyPlanAgent` propose un calendrier ; pour chaque item,
   `ContentReActAgent` produit légende + image.
8. **Schedule & Publish** : l'utilisateur connecte ses comptes (Meta/LinkedIn) puis planifie ;
   le worker `scheduled_publisher` envoie au moment voulu.
9. **Website Builder** : pipeline 5 phases en SSE → site Vercel déployé.
10. **Optimizer** : ETL collecte les KPIs ; l'agent recommande des optimisations.

### B. Cycle de publication planifiée
```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as backend-api
    participant W as Worker (thread)
    participant Meta as Meta Graph

    UI->>API: POST /scheduled-publications {generated_content_id, scheduled_at}
    API->>API: Snapshot caption + image_url
    API->>API: Insert status=scheduled
    loop Toutes les 30 s
        W->>API: SELECT * WHERE scheduled_at <= now() AND status='scheduled'
        W->>API: status=publishing, attempt_count++
        W->>Meta: POST /me/feed (token déchiffré)
        alt success
            W->>API: status=published, external_post_id
            W->>API: INSERT notification 'published'
        else error
            W->>API: status='failed' (si attempt >= 3) sinon retry
            W->>API: INSERT notification 'failed'
        end
    end
    UI->>API: SSE /notifications (push)
```

### C. Génération de site (SSE)
```
client                                AI orchestrator
  | POST /website/description/stream  |
  |---------------------------------->|  context  → fetch_context()
  |   event: step (status=done)       |
  |   event: step (design...)         |  Phase 2  → architecture + content
  |   event: step (persist)           |
  |   event: result {description}     |
  |<----------------------------------|

  | POST /website/generate/stream     |
  |---------------------------------->|  build    → coder_tool (HTML)
  |   event: step (qa)                |  qa       → validator_tool + auto-fix
  |   event: result {html, stats}     |
  |<----------------------------------|

  | POST /website/deploy              |
  |---------------------------------->|  vercel_deploy → URL publique
```

---

## 18. Scalabilité, Performance et Maintenabilité

### Scalabilité
- **Découplage des services** : front, API, IA scalent indépendamment.
- **Rotation multi-clés** sur tous les fournisseurs LLM (NVIDIA, Groq, HF) absorbe les rate-limits.
- **Asyncpg** pour les workloads lourds en concurrence (ETL).
- **SSE** au lieu de WebSocket : meilleur cache HTTP, simple à scaler horizontalement derrière
  un reverse proxy.
- **Worker en thread asyncio** dédié (n'interfère pas avec la boucle FastAPI).

### Performance
- LLM principal **gpt-oss-120b** servi par NVIDIA NIM (haute throughput).
- Cap sortie 65 536 tokens (suffisant pour HTML complet d'une page).
- Cloudinary CDN pour l'image (pas de re-upload depuis le frontend).
- Cache de la dernière recommandation Optimizer (évite des appels LLM redondants).
- **Snapshots** des publications planifiées : aucune lecture transverse au moment du publish.

### Maintenabilité
- Couche **services** systématique (pas de logique métier dans les routes).
- **Pydantic v2** côté schémas IO + ORM SQLAlchemy 2.0 (typed, mypy-friendly).
- **Alembic** comme source de vérité des migrations.
- **Prompts versionnés** dans `backend-ai/prompts/` (pas dans le code).
- **Tests** : répertoire `backend-ai/tests/` (à étoffer).
- **Pyright** strict mode (`backend-ai/pyrightconfig.json`).

---

## 19. Limitations Connues et Améliorations Futures

### Limitations actuelles
- **Pas de Dockerfile / CI/CD** versionné dans le repo (déploiement manuel).
- **Pas de file de tâches distribuée** (Celery / RQ / Arq) : le worker tourne dans le même
  process que l'API. Acceptable en mono-instance, à revoir pour scale-out.
- **Tests insuffisants** : couverture unitaire limitée, pas de tests E2E automatisés.
- **Couplage HTTP backend-ai → backend-api** : tout passe par REST authentifié JWT, ce qui
  ajoute de la latence pour les workflows lourds.
- **Pas de cache Redis** : les recommandations Optimizer sont cachées en DB uniquement.
- **Internationalisation partielle** : le clarifier détecte la langue, mais l'UI reste FR.
- **Stockage logo en base** (mediumtext) plutôt que sur CDN dans certains cas.

### Roadmap envisagée
- Conteneurisation **Docker Compose** (postgres, backend-api, backend-ai, frontend).
- **CI GitHub Actions** : lint + tests + build + push d'images.
- **Celery + Redis** pour découpler le worker de publication.
- **Cache Redis** + invalidation pour KPIs ETL et recommandations.
- **WebSocket** pour les notifications temps réel (en complément du SSE).
- **Tests E2E** avec Playwright sur les parcours critiques (création d'idée → site déployé).
- **Internationalisation** complète (i18next côté React).
- **Quotas et facturation** par utilisateur (rate-limit sur les agents les plus coûteux).
- **A/B testing** sur les recommandations Optimizer (mesure d'uplift réel).
- **Migration vers une vraie file d'événements** (NATS / Kafka) entre backend-api et backend-ai.

---

## Crédits

Projet de fin d'études (PFE) — **BrandAI**.
Stack basée sur FastAPI, LangChain/LangGraph, NVIDIA NIM, React 19, PostgreSQL.

Pour toute question technique, ouvrir une *issue* ou contacter l'équipe via le repository.
