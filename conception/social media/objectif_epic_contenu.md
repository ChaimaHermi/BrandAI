# Épic — Création, planification et publication automatique de contenu social

## Objectif

Permettre à l'utilisateur de produire et diffuser du contenu sur ses réseaux sociaux connectés (LinkedIn, Facebook, Instagram) sans rédaction manuelle ni gestion calendaire fastidieuse. L'épic couvre l'intégralité du cycle de vie d'une publication, de la simple idée formulée en langage naturel jusqu'à la mise en ligne effective sur la plateforme cible.

## Périmètre fonctionnel

Trois parcours utilisateur s'enchaînent et partagent la même infrastructure de génération :

1. **Génération à la demande** — l'utilisateur demande un post unique pour une plateforme et un objectif précis. Le système produit une légende adaptée aux contraintes de la plateforme et, si pertinent, une image cohérente avec le ton du projet.

2. **Plan de contenu hebdomadaire** — l'utilisateur exprime ses intentions en langage naturel (« annoncer le lancement, partager un témoignage client, présenter la nouvelle fonctionnalité »). Le LLM planificateur lit l'intention, en déduit le nombre exact de posts, choisit les plateformes adaptées à chaque message, propose une date et une heure différente par plateforme, et décide si une image accompagne chaque variante. L'utilisateur ajuste si besoin, puis approuve : le contenu est généré et programmé en bloc.

3. **Publication automatique** — un travailleur d'arrière-plan scrute en continu les publications programmées et les diffuse à l'heure prévue sur les plateformes ciblées via leurs API officielles (Meta Graph API pour Facebook/Instagram, LinkedIn UGC Posts API). L'utilisateur est notifié du résultat en temps réel.

À cela s'ajoute une vue calendrier qui permet de visualiser, reprogrammer ou annuler une publication tant qu'elle n'a pas été diffusée.

## Principes de conception

- **Génération paresseuse** — aucune légende ni image n'est produite avant l'approbation explicite de l'utilisateur ; les propositions de planification (plateformes, dates, heures, choix d'image) sont l'unique sortie du premier appel LLM, ce qui maintient le coût marginal d'une exploration faible.

- **Décision LLM, pas de défaut codé en dur** — le nombre de posts, les plateformes recommandées, l'heure optimale par plateforme et la nécessité d'une image par plateforme sont toutes des décisions du LLM raisonnées sur le contexte (audience cible, type de contenu, plateforme). Aucune valeur par défaut figée n'est appliquée silencieusement.

- **Garde-fou métier non négociable** — Instagram étant intrinsèquement visuel, une image y est obligatoire ; cette règle est appliquée à quatre niveaux (prompt LLM, normalisation serveur, génération du contenu, approbation finale) pour qu'aucun chemin technique ne puisse aboutir à une publication Instagram sans image.

- **Séparation des responsabilités** — Backend AI concentre la logique LLM et la génération de contenu ; Backend API gère la persistance, les connexions OAuth chiffrées, la programmation et la publication effective. Le travailleur de publication tourne dans le processus Backend API pour partager directement la base de données et les tokens.

- **Traçabilité** — chaque variante porte un champ `timing_source` qui enregistre l'origine de sa date et de son heure (utilisateur explicite, jour utilisateur + heure LLM, etc.), ce qui permet une attribution claire en cas d'analyse a posteriori.

## Acteurs et systèmes externes

- **Utilisateur entrepreneur** — déclenche les générations, valide ou ajuste les propositions, consulte ses publications passées et à venir.
- **Backend AI (FastAPI, port 8001)** — pipeline de génération, raisonnement LLM, orchestration des appels modèles.
- **Backend API (FastAPI, port 8000)** — persistance PostgreSQL, gestion des connexions sociales, travailleur de publication.
- **NVIDIA NIM** — modèle texte `openai/gpt-oss-120b` (légende, planification, prompts image) et modèle image `flux.2-klein-4b`.
- **Cloudinary** — hébergement public des images générées (URL HTTPS stable requise par les API Meta et LinkedIn).
- **Meta Graph API v22.0** — publication Facebook et Instagram.
- **LinkedIn UGC Posts API** — publication LinkedIn.

## Critères d'acceptation de l'épic

- L'utilisateur peut générer une publication unique sur une plateforme choisie en moins d'une minute, légende et image incluses.
- À partir d'un prompt en langage naturel, le système propose un plan hebdomadaire dont le nombre de posts reflète exactement les intentions exprimées (pas de valeur par défaut).
- L'utilisateur peut, avant approbation, modifier la plateforme, la date, l'heure ou la présence d'image de chaque variante, à l'exception d'Instagram dont l'image est verrouillée par contrat.
- Après approbation, chaque publication programmée est diffusée à la minute prévue, sans intervention manuelle, et l'utilisateur reçoit une notification de succès ou d'échec.
- Une publication non encore diffusée peut être reprogrammée ou annulée depuis la vue calendrier.
