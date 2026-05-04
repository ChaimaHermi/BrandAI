from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    runpy.run_path(str(root / "normalize_facebook.py"), run_name="__main__")
    runpy.run_path(str(root / "normalize_instagram.py"), run_name="__main__")
    runpy.run_path(str(root / "normalize_linkedin.py"), run_name="__main__")


if __name__ == "__main__":
    main()
