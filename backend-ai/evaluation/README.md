# Évaluation LangSmith — BrandAI

Projet LangSmith par défaut : **`brand-ai-eval`** (override : `LANGCHAIN_EVAL_PROJECT` dans `.env`).

## Prérequis

Dans `Brand AI/.env` :

```env
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
AZURE_OPENAI_API_KEY=...   # judges LLM (analyse de marché)
```

---

## 1. Clarification de l'idée

```powershell
cd backend-ai
python evaluation/clarifier_eval.py --replace
```

| LangSmith | Valeur |
|-----------|--------|
| Dataset | `brandai-clarifier-clarification-idee` |
| Script | `clarification-de-lidee/clarifier_eval.py` |
| Métriques | `status_correctness`, `format_compliance`, `brief_completeness`, `questions_relevance`, `brief_coherence` |
| Dernière exp. | `clarification-5-metrics-v3-…` |

**UI :** Datasets → `brandai-clarifier-clarification-idee` → onglet **Experiments**

---

## 2. Analyse de marché (graph complet)

```powershell
python evaluation/market_eval.py --replace --prefix market-analysis-v4 --concurrency 1
```

| LangSmith | Valeur |
|-----------|--------|
| Dataset | `brandai-market-analyse-de-marche` |
| Golden | `analyse-de-marche/market_golden.jsonl` (5 idées) |
| Métriques | 19 scores : `format_compliance`, `context_coherence`, `faithfulness` (par agent) |
| Dernière exp. | `market-analysis-v3-e97c36a4` |

| **Évaluation finale (tableau complet)** | `resultat-final-complet-fef19ca9` (5/5 OK, ~23 min) |

```powershell
python evaluation/market_eval.py --no-upload --prefix resultat-final-complet --concurrency 1
```

**UI :** Datasets → `brandai-market-analyse-de-marche` → **Experiments** → `resultat-final-complet-fef19ca9`

Lien direct :
https://smith.langchain.com/o/83414628-8f17-4810-b651-0bba575729f2/datasets/f2adcaed-c00b-4ee5-aadb-074e6206d20d/compare?selectedSessions=078a2d67-6604-4136-bb58-043af73036f3

---

## 3. VOC Agent seul

```powershell
python evaluation/voc_eval.py --replace --prefix voc-analysis-v1 --concurrency 1
```

| LangSmith | Valeur |
|-----------|--------|
| Dataset | `brandai-voc-eval` |
| Golden | même `market_golden.jsonl` (5 idées) |
| Métriques | `voc_format_compliance`, `voc_context_coherence`, `voc_faithfulness` |
| Dernière exp. | `voc-analysis-v1-27e3a668` |

**UI :** Datasets → `brandai-voc-eval` → **Experiments**

Lien direct dernière expérience VOC :
https://smith.langchain.com/o/83414628-8f17-4810-b651-0bba575729f2/datasets/2fd6c2b0-9c0c-456a-a5ec-e18bab11cafc/compare?selectedSessions=25435860-a9e3-4a5d-963b-1e7b7ed15438

---

## Options communes

| Flag | Effet |
|------|-------|
| `--replace` | Remplace les exemples du dataset (évite les doublons) |
| `--upload-only` | Crée/met à jour le dataset sans appeler les LLM |
| `--no-upload` | Relance une expérience sur le dataset existant |
| `--prefix mon-exp` | Nom de l'expérience dans LangSmith |
| `--concurrency 1` | Recommandé (quota Tavily/SerpAPI) |

> **Ne pas créer de judges dans l'UI LangSmith** — cela provoque des colonnes `score` parasites et des « All Failed ». Utiliser uniquement les evaluators Python.

**Métriques retenues (analyse de marché) :**
- `*_format_compliance` — schéma JSON / champs obligatoires (déterministe)
- `*_context_coherence` — LLM-as-judge (cohérence avec l'idée)
- `*_faithfulness` — LLM-as-judge (ancrage dans le corpus Tavily)

## Fichiers

| Fichier | Rôle |
|---------|------|
| `clarification-de-lidee/clarifier_golden.jsonl` | Golden clarifier (25 cas) |
| `clarifier_eval.py` | Eval clarification |
| `analyse-de-marche/market_golden.jsonl` | Golden marché (5 cas) |
| `market_eval.py` | Eval graph marché complet |
| `voc_eval.py` | Eval VOC seul |
| `analyse-de-marche/llm_judge_evaluators.py` | Judges LLM (context + faithfulness) |
