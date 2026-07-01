#!/usr/bin/env python3
"""PEP FX task entrypoint — delegates to fx_organic_growth archetype verifier."""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_GT = (
    Path(__file__).resolve().parent.parent / "ground_truth" / "PEP_fx_organic_growth_gt.json"
)

if __name__ == "__main__":
    from verify_fx_organic_growth import main as fx_main

    sys.argv = [sys.argv[0], "--ground-truth", str(DEFAULT_GT), *sys.argv[1:]]
    sys.exit(fx_main())
