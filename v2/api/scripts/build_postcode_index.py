"""
Build an enriched postcode parquet with (pcds, ladcd, ladnm, lat, lng).

Source: Code-Point Open shapefile under data/geodata/Code-Point London (shapefile)/.
The shapefile uses British National Grid (EPSG:27700); we project to WGS84
(EPSG:4326) to get lat/lng.

Run once locally before deploying:

    pip install -e .[build]
    python scripts/build_postcode_index.py

Output: app/data/postcodes.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd


def main() -> None:
    api_dir = Path(__file__).resolve().parents[1]
    repo_dir = api_dir.parents[1]
    shp = (
        repo_dir
        / "data"
        / "geodata"
        / "Code-Point London (shapefile)"
        / "CodePointOpen_London_201709.shp"
    )
    base_csv = repo_dir / "data" / "geodata" / "post_code" / "london_post_code_data.csv"
    out = api_dir / "app" / "data" / "postcodes.parquet"

    if not shp.exists():
        sys.exit(f"Missing shapefile: {shp}")
    if not base_csv.exists():
        sys.exit(f"Missing base CSV: {base_csv}")

    print(f"Reading {shp.name}...")
    gdf = gpd.read_file(shp)
    # Code-Point Open columns vary by release; the postcode column is typically 'Postcode' or 'POSTCODE'.
    pc_col = next((c for c in gdf.columns if c.lower() == "postcode"), None)
    if pc_col is None:
        sys.exit(f"Could not find a postcode column in shapefile. Columns: {list(gdf.columns)}")

    if gdf.crs is None:
        gdf = gdf.set_crs(27700)
    gdf = gdf.to_crs(4326)
    gdf["lng"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    coords = gdf[[pc_col, "lat", "lng"]].rename(columns={pc_col: "pcds"})
    # Normalize whitespace in postcodes (Code-Point Open uses a fixed-width 7-char form).
    coords["pcds"] = coords["pcds"].str.strip().str.replace(r"\s+", " ", regex=True).str.upper()

    print(f"Reading {base_csv.name}...")
    base = pd.read_csv(base_csv, dtype={"pcds": str, "ladcd": str, "ladnm": str})
    base["pcds"] = base["pcds"].str.strip().str.upper()

    merged = base.merge(coords, on="pcds", how="left")
    missing = merged["lat"].isna().sum()
    print(f"Postcodes total: {len(merged):,}  missing lat/lng: {missing:,}")

    out.parent.mkdir(parents=True, exist_ok=True)
    merged[["pcds", "ladcd", "ladnm", "lat", "lng"]].to_parquet(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
