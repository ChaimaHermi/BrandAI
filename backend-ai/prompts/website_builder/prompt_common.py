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
AUTO-VERIFICATION OBLIGATOIRE — AVANT DE RÉPONDRE, VÉRIFIE CHAQUE POINT :

✅ STRUCTURE
- [ ] Le document commence EXACTEMENT par <!DOCTYPE html> (rien avant)
- [ ] Le document se termine EXACTEMENT par </html> (rien après)
- [ ] <head> contient : charset, viewport, title, Tailwind CDN, Google Fonts, Lucide CDN
- [ ] <body> contient toutes les sections de l'architecture, dans l'ordre

✅ NAVIGATION
- [ ] Chaque lien de menu utilise href="#id-section" (jamais href="#" seul)
- [ ] Chaque href="#x" a un id="x" correspondant dans le document
- [ ] Le header est en position fixed avec z-50

✅ BRAND KIT
- [ ] Le nom de marque apparaît dans le header ET dans le footer
- [ ] Le slogan apparaît mot pour mot dans le hero
- [ ] Les couleurs du brand kit sont dans tailwind.config (primary, secondary, accent...)
- [ ] Les polices Google Fonts du brand kit sont chargées et utilisées

✅ RESPONSIVE
- [ ] <meta name="viewport"> présent dans <head>
- [ ] Chaque grille utilise grid-cols-1 md:grid-cols-2 lg:grid-cols-3
- [ ] Menu mobile (hamburger) présent et fonctionnel

✅ SORTIE PROPRE
- [ ] AUCUN texte, commentaire ou explication en dehors du HTML
- [ ] AUCUNE balise markdown (pas de ```html)
- [ ] AUCUNE URL d'image inventée (unsplash, picsum, placeholder...)
""".strip()

