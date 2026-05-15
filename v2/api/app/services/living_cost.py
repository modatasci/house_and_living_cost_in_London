"""
Council tax + rent lookups by borough.

Adapted from src/get_living_cost.py: same CSV inputs, simpler API
(borough-keyed rather than postcode-keyed — postcode -> borough is handled
upstream by PostcodeService).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.config import settings


def _normalize_borough(name: str) -> str:
    return name.lower().replace(" ", "").replace("&", "").replace("and", "")


class LivingCostService:
    def __init__(self, data_dir: Path):
        self.council_tax = pd.read_csv(data_dir / "council_tax" / "council_tax_2024_2025.csv")
        self.rent = pd.read_csv(data_dir / "rent_price" / "londonrent.csv")
        self._rent_map = {_normalize_borough(b): b for b in self.rent["Borough"].unique()}

    # --- council tax ---

    def council_tax_monthly(self, borough_code: str, band: str = "D") -> float | None:
        col = f"Band {band.upper()}"
        row = self.council_tax[self.council_tax["Code"] == borough_code]
        if row.empty or col not in row.columns:
            return None
        annual = float(row.iloc[0][col])
        return round(annual / 12, 2)

    # --- rent ---

    def _match_rent_borough(self, borough_name: str) -> str | None:
        return self._rent_map.get(_normalize_borough(borough_name))

    def rent_monthly(
        self, borough_name: str, bedroom_category: str = "One Bedroom"
    ) -> dict[str, float | None] | None:
        matched = self._match_rent_borough(borough_name)
        if not matched:
            return None
        sub = self.rent[
            (self.rent["Borough"] == matched)
            & (self.rent["Bedroom Category"] == bedroom_category)
        ]
        if sub.empty:
            return None
        row = sub.iloc[0]

        def _num(v) -> float | None:
            s = str(v).strip()
            if s in ("..", "-", "nan", ""):
                return None
            try:
                return float(s.replace(",", ""))
            except ValueError:
                return None

        return {
            "median": _num(row["Median"]),
            "lower_quartile": _num(row["Lower quartile"]),
            "upper_quartile": _num(row["Upper quartile"]),
            "mean": _num(row["Mean"]),
        }


@lru_cache(maxsize=1)
def get_living_cost_service() -> LivingCostService:
    return LivingCostService(settings.resolved_data_dir)
