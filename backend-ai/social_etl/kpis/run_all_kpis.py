from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config.database import create_db_pool
from social_etl.kpis.facebook_kpis import compute_facebook_kpis
from social_etl.kpis.instagram_kpis import compute_instagram_kpis
from social_etl.kpis.linkedin_kpis import compute_linkedin_kpis

logger = logging.getLogger(__name__)


async def run_all_kpis(*, parallel: bool = False) -> dict[str, int]:
    pool = await create_db_pool()
    try:
        if parallel:
            fb_count, ig_count, li_count = await asyncio.gather(
                compute_facebook_kpis(pool),
                compute_instagram_kpis(pool),
                compute_linkedin_kpis(pool),
            )
        else:
            fb_count = await compute_facebook_kpis(pool)
            ig_count = await compute_instagram_kpis(pool)
            li_count = await compute_linkedin_kpis(pool)
    except Exception:
        logger.exception("kpi run failed")
        raise
    finally:
        await pool.close()

    return {
        "facebook_connections": fb_count,
        "instagram_connections": ig_count,
        "linkedin_connections": li_count,
        "total_connections": fb_count + ig_count + li_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcule et upsert les KPIs 30 jours pour Facebook, Instagram et LinkedIn."
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Lance les calculs des 3 plateformes en parallele.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    results = asyncio.run(run_all_kpis(parallel=args.parallel))
    logger.info("kpi run complete: %s", results)
    print(results)


if __name__ == "__main__":
    main()
