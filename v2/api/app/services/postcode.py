"""
Postcode lookup service.

Loads the London postcode CSV (pcds, ladcd, ladnm) into memory once at startup.
If an enriched parquet with lat/lng exists (built by scripts/build_postcode_index.py),
also loads it and builds a KD-tree for reverse geocoding from map clicks.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import pandas as pd
import numpy as np

from app.config import settings


def _normalize(pc: str) -> str:
    return pc.replace(" ", "").upper().strip()


class PostcodeService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.df = self._load_base()
        self._norm_index: dict[str, int] = {
            _normalize(pc): i for i, pc in enumerate(self.df["pcds"].tolist())
        }
        self.coords_df, self._kdtree = self._load_coords()

    def _load_base(self) -> pd.DataFrame:
        path = self.data_dir / "geodata" / "post_code" / "london_post_code_data.csv"
        df = pd.read_csv(path, dtype={"pcds": str, "ladcd": str, "ladnm": str})
        return df

    def _load_coords(self):
        """Try to load the enriched parquet (postcode + lat/lng). Return (df, kdtree) or (None, None)."""
        parquet = self.data_dir.parent / "v2" / "api" / "app" / "data" / "postcodes.parquet"
        if not parquet.exists():
            # Also accept a parquet sitting in the standard data dir
            alt = self.data_dir / "geodata" / "post_code" / "postcodes_enriched.parquet"
            parquet = alt if alt.exists() else None
        if parquet is None or not parquet.exists():
            return None, None
        try:
            coords = pd.read_parquet(parquet)
        except Exception:
            return None, None
        from scipy.spatial import cKDTree

        pts = np.deg2rad(coords[["lat", "lng"]].to_numpy())
        # Use approximate planar tree on radians; fine for distances within Greater London.
        tree = cKDTree(pts)
        return coords, tree

    # --- public API ---

    def lookup(self, postcode: str) -> dict | None:
        idx = self._norm_index.get(_normalize(postcode))
        if idx is None:
            return None
        row = self.df.iloc[idx]
        out = {
            "postcode": row["pcds"],
            "borough_code": row["ladcd"],
            "borough_name": row["ladnm"],
            "lat": None,
            "lng": None,
        }
        if self.coords_df is not None:
            match = self.coords_df[self.coords_df["pcds"] == row["pcds"]]
            if not match.empty:
                out["lat"] = float(match.iloc[0]["lat"])
                out["lng"] = float(match.iloc[0]["lng"])
        return out

    def search(self, query: str, limit: int = 10) -> list[dict]:
        if not query:
            return []
        q = _normalize(query)
        # Prefix match on normalized postcode.
        mask = self.df["pcds"].str.replace(" ", "", regex=False).str.upper().str.startswith(q)
        hits = self.df[mask].head(limit)
        results = []
        for _, row in hits.iterrows():
            entry = self.lookup(row["pcds"])
            if entry:
                results.append(entry)
        return results

    def nearest(self, lat: float, lng: float) -> dict | None:
        if self._kdtree is None or self.coords_df is None:
            return None
        pt = np.deg2rad(np.array([[lat, lng]]))
        _, idx = self._kdtree.query(pt, k=1)
        row = self.coords_df.iloc[int(idx[0])]
        return self.lookup(row["pcds"])

    def has_coords(self) -> bool:
        return self._kdtree is not None


@lru_cache(maxsize=1)
def get_postcode_service() -> PostcodeService:
    return PostcodeService(settings.resolved_data_dir)
