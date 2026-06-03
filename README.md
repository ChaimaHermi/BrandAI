# BrandAI

BrandAI est une plateforme basée sur l’intelligence artificielle générative. Elle accompagne les porteurs de projets et les startups dans la construction de leur présence digitale : clarification de l’idée, analyse de marché, plan marketing, identité de marque, site web vitrine, contenu social, publication planifiée, suivi des performances et recommandations.

## Contexte du projet

Ce projet a été réalisé dans le cadre d’un Projet de Fin d’Études au sein de **Talan Tunisie Consulting**, département **Talan Innovation Factory**.

## Objectifs

- Centraliser le parcours de lancement digital dans une seule plateforme.
- Maintenir la cohérence entre l’idée, l’analyse de marché, l’identité de marque, le site et les contenus sociaux.
- Automatiser les étapes grâce à des agents IA spécialisés (LangChain / LangGraph).
- Fournir des recommandations à partir des indicateurs collectés sur les réseaux sociaux.

## Fonctionnalités implémentées

### 1. Clarification de l’idée

- Soumission d’une idée de projet.
- Contrôle de sécurité (Llama Guard) et détection de contenu inapproprié.
- Questions de clarification si le score de clarté est insuffisant.
- Production d’un brief structuré (pitch, cible, secteur, géographie) persisté en base.

### 2. Analyse de marché

Pipeline multi-agents (LangGraph) :

- extraction des mots-clés ;
- estimation de la taille du marché ;
- analyse concurrentielle ;
- analyse de la voix du client (VOC) ;
- tendances et risques ;
- analyse stratégique.

Résultats affichés dans l’interface avec sources de recherche (Tavily, SerpAPI, scraping).

### 3. Plan marketing

Génération d’un plan marketing à partir de l’idée clarifiée et de l’analyse de marché, enregistré et consultable dans l’application.

### 4. Identité de marque

Génération séquentielle d’un brand kit :

- propositions de noms (vérification via Brandfetch) ;
- slogans ;
- palette de couleurs ;
- logo (génération d’image IA, upload CDN).

### 5. Site web vitrine

- Génération du site (architecture, contenus, HTML/Tailwind/JS) en streaming (SSE).
- Prévisualisation dans l’interface.
- Déploiement sur Vercel.

### 6. Gestion des réseaux sociaux

- Connexion OAuth : **Facebook**, **Instagram** (Meta), **LinkedIn**.
- Plan de publication hebdomadaire généré par IA.
- Génération de posts par plateforme (texte + image, agent ReAct).
- Planification et publication automatique via un worker planifié (`scheduled_publisher`).
- Historique des contenus générés.

### 7. Suivi des performances et recommandations

- Pipeline ETL des publications (Facebook, Instagram, LinkedIn via Apify).
- Calcul et affichage des KPIs.
- Recommandations stratégiques générées par l’agent Social Optimizer.

### Authentification

- Inscription et connexion par email / mot de passe (JWT).
- Connexion Google OAuth.

## Technologies utilisées

| Composant        | Technologies                                              |
| ---------------- | --------------------------------------------------------- |
| Frontend         | React 19, Vite                                            |
| API métier       | FastAPI, SQLAlchemy, Alembic — `backend-api` (port 8000)  |
| Serveur IA       | FastAPI, LangChain, LangGraph — `backend-ai` (port 8001)  |
| Base de données  | PostgreSQL                                                |
| LLM              | NVIDIA NIM (`gpt-oss-120b`), Groq (fallback / garde-fous) |
| Images           | Hugging Face, Pollinations, Cloudinary                    |
| Déploiement site | Vercel API                                                |
| Auth sociale     | Meta Graph API, LinkedIn API, Google OAuth                |

## Structure du projet

```
Brand AI/
├── backend-api/          # API REST, auth, persistance, worker publications
├── backend-ai/           # Agents IA, prompts, outils
├── frontend/             # Interface React
├── .env                  # Variables d'environnement (racine, non versionné)
└── README.md
```

## Installation

### Prérequis

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+

### 1. Cloner le projet

```bash
git clone <url-du-depot>
cd "Brand AI"
```

### 2. Variables d’environnement

Créer un fichier `.env` à la racine du projet (utilisé par `backend-api` et `backend-ai`).

Exemple minimal :

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/brandai
SECRET_KEY=change-me
FRONTEND_URL=http://localhost:5173

NVIDIA_API_KEY_1=nvapi-...
GROQ_API_KEY=gsk_...

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

TAVILY_API_KEY=...
SERPAPI_API_KEY=...

CONTENT_CLOUDINARY_CLOUD_NAME=...
CONTENT_CLOUDINARY_API_KEY=...
CONTENT_CLOUDINARY_API_SECRET=...

LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...

VERCEL_TOKEN=...
```

Créer aussi `frontend/.env` :

```env
VITE_API_URL=http://localhost:8000/api
VITE_AI_URL=http://localhost:8001/api/ai
```

### 3. Base de données

```bash
createdb brandai
```

### 4. Backend API

```bash
cd backend-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 5. Backend IA

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
npm run dev
```

Ouvrir `http://localhost:5173`.

## Utilisation

1. Créer un compte ou se connecter (email ou Google).
2. Soumettre une idée et compléter la clarification si nécessaire.
3. Lancer l’analyse de marché et consulter les résultats.
4. Générer le plan marketing.
5. Créer l’identité de marque (nom, slogan, palette, logo).
6. Générer le site vitrine, prévisualiser et déployer sur Vercel.
7. Connecter Facebook, Instagram ou LinkedIn.
8. Générer le plan hebdomadaire et les posts, puis planifier ou publier.
9. Lancer l’ETL social et consulter les KPIs et recommandations.

## Agents IA

| Module        | Agents                                                                               |
| ------------- | ------------------------------------------------------------------------------------ |
| Clarification | Idea Clarifier (+ Llama Guard)                                                       |
| Marché        | Keyword Extractor, Market Sizing, Competitor, VOC, Trends & Risks, Strategy Analysis |
| Marketing     | Marketing Plan Agent                                                                 |
| Marque        | Name, Slogan, Palette, Logo (ReAct)                                                  |
| Contenu       | Weekly Plan, Content ReAct (légende + image par plateforme)                          |
| Site          | Website Builder (orchestrateur multi-phases)                                         |
| Optimisation  | Social ETL + Recommendation Agent                                                    |

## Sécurité

- Clés API et secrets dans `.env` (non versionné).
- Tokens OAuth sociaux chiffrés en base.
- Authentification JWT entre le frontend et les backends.
- Validation utilisateur avant publication des contenus générés.

## Auteur

**Chaima Hermi**  
Projet de Fin d’Études — Ingénierie en Informatique et Multimédia  
Année universitaire : 2025–2026

## Encadrement

- Encadrant académique : Prof. Mohamed Mohsen Gammoudi
- Responsable Innovation Factory : Imen Ayari
- Encadrantes en entreprise : Amel Kouki, Afef Abbasi

## Licence

Projet académique. Toute réutilisation doit respecter les règles de confidentialité, de propriété intellectuelle et les autorisations de l’établissement et de l’entreprise d’accueil.
