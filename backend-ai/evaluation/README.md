# Évaluation LangSmith — Idea Clarifier

## Prérequis

Dans `Brand AI/.env` :

```env
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
```

Clés NVIDIA requises (`NVIDIA_API_KEY_1` …) — le clarifier utilise `openai/gpt-oss-120b`.

## Lancer

```powershell
cd backend-ai
python evaluation/clarifier_eval.py --replace
```

- `--replace` : remplace les exemples du dataset (évite les doublons)
- `--upload-only` : crée le dataset sans appeler les LLM
- `--no-upload` : relance une expérience sur le dataset existant
- `--prefix clarifier-v2` : nom de l'expérience dans LangSmith

## Voir les résultats

1. [smith.langchain.com](https://smith.langchain.com)
2. Projet **`brand-ai-eval`** (defaut du script; override: `LANGCHAIN_EVAL_PROJECT=...` dans `.env`)
3. **Datasets** → `brandai-clarifier-golden` → **Experiments**
4. Ouvrir la dernière expérience (`clarifier-v1-…`)
5. Scores : `type_match`, `clarified_complete`, `json_type_valid`
6. Clic sur une ligne → **Trace** pour le détail (Llama Guard, `brandai.llm_call`)

## Fichiers

| Fichier | Rôle |
|---------|------|
| `clarifier_golden.jsonl` | Cas de test (inputs + expected_type) |
| `clarifier_eval.py` | Upload dataset + `evaluate()` |
