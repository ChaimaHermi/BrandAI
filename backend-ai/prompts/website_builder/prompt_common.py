"""
Règles communes des prompts Website Builder pour éviter la duplication.
"""

HTML_OUTPUT_CONTRACT = """
CONTRAT DE SORTIE — STRICT
- Renvoie UNIQUEMENT un document HTML complet, de `<!DOCTYPE html>` à `</html>`.
- Aucun texte avant/après le HTML.
- Aucune balise markdown (pas de ```html).
- Ne renvoie jamais d'erreur textuelle.
""".strip()


NAVIGATION_INVARIANTS = """
INVARIANTS NAVIGATION (NON NEGOCIABLES)
1) Chaque section cible de navigation possède un id unique, en slug minuscule.
2) Tous les liens de menu pointent vers des ids réels: href="#section-id".
3) Tous les CTA avec cible pointent vers des ids réels: href="#target-id".
4) Ajouter `style="scroll-margin-top: 80px;"` sur les sections ciblées.
5) Ajouter `html { scroll-behavior: smooth; }` dans le style global.
""".strip()


QUALITY_SELF_CHECK = """
AUTO-VERIFICATION INTERNE AVANT REPONSE
- Le HTML commence bien par <!DOCTYPE html> et se termine par </html>.
- Aucun href="#" vide pour les liens de navigation/CTA.
- Chaque href="#x" a bien un id="x" dans le document.
- Aucune section obligatoire de la description n'est omise.
- Aucune phrase hors HTML n'est ajoutée en sortie.
""".strip()

