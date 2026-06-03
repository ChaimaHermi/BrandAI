"""
Données fixes pour la démo vidéo / rapport (marque Repido — livraison de repas, Tunisie).
Activé via BRANDING_DEMO_MODE=1 dans .env.
"""

from __future__ import annotations

from typing import Any

REPIDO_LOGO_URL = (
    "https://res.cloudinary.com/dcy7tebnz/image/upload/"
    "v1778838264/brandai/logo-originality/26f1117139a1379c8e3ee0c33345e26e3a9a4fdd.jpg"
)

_DEMO_NAMES: list[dict[str, str]] = [
    {
        "name": "Repido",
        "description": (
            "Nom inventé évoquant la rapidité et la commande de repas. Il est court, "
            "percutant et facile à retenir, parfaitement adapté à une application mobile tunisienne."
        ),
        "availability": "not_exists",
    },
    {
        "name": "Mangevite",
        "description": (
            "Nom descriptif et bénéfice-client qui combine « manger » et « vite », mettant en avant "
            "la promesse d'un service de repas rapide et simple."
        ),
        "availability": "not_exists",
    },
    {
        "name": "TuniPlat",
        "description": (
            "Nom hybride associant « Tuni » pour la Tunisie et « Plat » pour les repas, signifiant "
            "une solution locale et spécialisée dans la livraison de plats."
        ),
        "availability": "not_exists",
    },
]

_DEMO_SLOGANS: list[dict[str, str]] = [
    {
        "text": "Repido, la faim n'attend plus",
        "rationale": "Accroche mémorable qui lie la marque à l'urgence de se restaurer.",
    },
    {
        "text": "Vos plats préférés, livrés à toute vitesse",
        "rationale": "Promesse claire de rapidité et de choix pour la cible urbaine tunisienne.",
    },
    {
        "text": "La Tunisie dans votre assiette, sans attendre",
        "rationale": "Ancrage local et bénéfice vitesse pour différencier l'offre.",
    },
]

_MEDITERRANEAN_SWATCHES: list[dict[str, str]] = [
    {
        "name": "Terracotta profond",
        "hex": "#B4342F",
        "role": "primary",
        "rationale": "Couleur signature — en-tête, logo et éléments d'identité forts.",
    },
    {
        "name": "Orange brûlé",
        "hex": "#D96C3A",
        "role": "secondary",
        "rationale": "Sections hero et blocs de mise en avant chaleureux.",
    },
    {
        "name": "Jaune safran",
        "hex": "#FFD15C",
        "role": "accent",
        "rationale": "Boutons CTA, badges et micro-interactions.",
    },
    {
        "name": "Crème",
        "hex": "#FFF9F2",
        "role": "background",
        "rationale": "Fond de page et zones respirantes.",
    },
    {
        "name": "Sable",
        "hex": "#F5E2C6",
        "role": "surface",
        "rationale": "Cartes, encarts et surfaces secondaires.",
    },
    {
        "name": "Espresso",
        "hex": "#2F1B17",
        "role": "text",
        "rationale": "Textes principaux et contrastes lisibles.",
    },
]

_MEDITERRANEAN_DESCRIPTION = (
    "Harmonie analogique inspirée des couleurs chaudes et authentiques du bassin "
    "méditerranéen, rattachant la marque à la culture tunisienne. Utilisez un en-tête "
    "vibrant, des sections terracotta et le jaune safran pour les boutons d'appel à l'action."
)


def build_demo_naming_identity() -> dict[str, Any]:
    return {
        "name_options": [dict(x) for x in _DEMO_NAMES],
        "branding_status": "partial",
    }


def build_demo_slogan_identity(brand_name: str) -> dict[str, Any]:
    slogans = [dict(s) for s in _DEMO_SLOGANS]
    if brand_name and brand_name.strip().lower() != "repido":
        slogans[0] = {
            "text": f"{brand_name.strip()}, la faim n'attend plus",
            "rationale": slogans[0]["rationale"],
        }
    return {
        "slogan_options": slogans,
        "chosen_brand_name": (brand_name or "Repido").strip(),
        "branding_status": "partial",
    }


def _mediterranean_palette() -> dict[str, Any]:
    return {
        "palette_name": "Express Méditerranée",
        "palette_description": _MEDITERRANEAN_DESCRIPTION,
        "swatches": [dict(s) for s in _MEDITERRANEAN_SWATCHES],
    }


def build_demo_palette_identity(brand_name: str) -> dict[str, Any]:
    main = _mediterranean_palette()
    return {
        "palette_options": [
            main,
            {
                "palette_name": "Soleil urbain",
                "palette_description": (
                    "Triade chaude pour une app de livraison dynamique : contraste fort "
                    "entre primaire et accent pour les CTA."
                ),
                "swatches": main["swatches"][:4]
                + [{"name": "Anthracite", "hex": "#1C1412", "role": "text", "rationale": "Textes UI."}],
            },
            {
                "palette_name": "Marché local",
                "palette_description": (
                    "Tons terre et épices rappelant les souks — cohérent avec une offre "
                    "de plats tunisiens authentiques."
                ),
                "swatches": [
                    {"name": "Rouge épice", "hex": "#A83228", "role": "primary", "rationale": "Header."},
                    {"name": "Ocre", "hex": "#C4783A", "role": "secondary", "rationale": "Sections."},
                    {"name": "Miel", "hex": "#E8B84A", "role": "accent", "rationale": "CTA."},
                    {"name": "Lin", "hex": "#FAF6EE", "role": "background", "rationale": "Fond."},
                ],
            },
        ],
        "color_palette": main,
        "chosen_brand_name": (brand_name or "Repido").strip(),
        "branding_status": "partial",
    }


def build_demo_logo_identity(brand_name: str) -> dict[str, Any]:
    name = (brand_name or "Repido").strip()
    model = "flux.2-klein-4b"
    return {
        "logo_concepts": [
            {
                "title": "Repido — scooter livraison",
                "image_prompt": (
                    f"Logo minimaliste pour {name}, service de livraison de repas en Tunisie, "
                    "scooter de livraison, palette terracotta et jaune safran, fond crème."
                ),
                "negative_prompt": "texte illisible, watermark, photo réaliste",
                "image_url": REPIDO_LOGO_URL,
                "image_provider": "nvidia",
                "image_model": model,
                "image_attribution": f"Image générée avec NVIDIA NIM — modèle {model}.",
            }
        ],
        "cloudinary_url": REPIDO_LOGO_URL,
        "chosen_brand_name": name,
        "branding_status": "partial",
    }
