"""Helper CLI conserve pour compatibilite (rarement utilise en production)."""

from __future__ import annotations


def main() -> None:
    raise RuntimeError(
        "Utiliser le pipeline complet via app.social_etl.pipeline.run_pipeline_async."
    )


if __name__ == "__main__":
    main()
