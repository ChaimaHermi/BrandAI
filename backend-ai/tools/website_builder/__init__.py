"""
Website Builder - Pipeline de generation de site vitrine.

Structure par phase :
  context/      Phase 1  - Chargement du contexte brand kit
  concept/      Phase 2  - Architecture + contenu + raffinement (GLM-5.1)
  generation/   Phase 3  - Generation HTML/Tailwind/JS (GLM-5.1)
  revision/     Phase 4  - Revision HTML par chat (GLM-5.1)
  deployment/   Phase 5  - Deploiement Vercel
  qa/           QA       - Validation et correction HTML
  infra/        Support  - SSE streaming, persistance, telemetrie LangSmith
"""
