from __future__ import annotations

import runpy
from pathlib import Path

from kpi_common import KPI_DIR, dump_json, load_json


def main() -> None:
    root = Path(__file__).resolve().parent
    runpy.run_path(str(root / "compute_facebook_kpis.py"), run_name="__main__")
    runpy.run_path(str(root / "compute_instagram_kpis.py"), run_name="__main__")
    runpy.run_path(str(root / "compute_linkedin_kpis.py"), run_name="__main__")

    combined = {
        "facebook": load_json(KPI_DIR / "facebook_kpis.json"),
        "instagram": load_json(KPI_DIR / "instagram_kpis.json"),
        "linkedin": load_json(KPI_DIR / "linkedin_kpis.json"),
    }
    out_path = KPI_DIR / "social_kpis_by_platform.json"
    dump_json(out_path, combined)
    print(f"all kpis -> {out_path}")


if __name__ == "__main__":
    main()
