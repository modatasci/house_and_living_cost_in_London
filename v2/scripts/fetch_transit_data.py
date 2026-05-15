"""
Fetch TfL transit data and write to v2/web/public/ as GeoJSON.

Sources:
  - Lines:    Overpass API (OSM route_master relations carry name + colour)
  - Stations: TfL ArcGIS Open Data portal

Run from repo root:
  python v2/scripts/fetch_transit_data.py
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import requests

OUT_DIR = Path(__file__).parent.parent / "web" / "public"

# ---------------------------------------------------------------------------
# TfL official line colours (fallback if OSM colour tag missing)
# ---------------------------------------------------------------------------
TFL_COLORS: dict[str, str] = {
    "bakerloo": "#B36305",
    "central": "#E32017",
    "circle": "#FFD300",
    "district": "#00782A",
    "hammersmith & city": "#F3A9BB",
    "hammersmith and city": "#F3A9BB",
    "jubilee": "#A0A5A9",
    "metropolitan": "#9B0056",
    "northern": "#000000",
    "piccadilly": "#003688",
    "victoria": "#0098D4",
    "waterloo & city": "#95CDBA",
    "waterloo and city": "#95CDBA",
    "elizabeth": "#7156A5",
    "elizabeth line": "#7156A5",
    "london overground": "#EE7C0E",
    "overground": "#EE7C0E",
    "dlr": "#00A4A7",
    "docklands light railway": "#00A4A7",
    # Overground line names (rebranded Nov 2024)
    "liberty line": "#5D6061",
    "lioness line": "#FAA61A",
    "mildmay line": "#0077AD",
    "suffragette line": "#76B82A",
    "weaver line": "#823E55",
    "windrush line": "#EE2E24",
}

def colour_for(name: str, osm_colour: str | None) -> str:
    if osm_colour and osm_colour.startswith("#"):
        return osm_colour
    return TFL_COLORS.get(name.lower(), "#888888")


# ---------------------------------------------------------------------------
# 1. Fetch line routes from Overpass
# ---------------------------------------------------------------------------
# Rotated on failure — public mirrors are individually flaky / rate-limited.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


def overpass_fetch(query: str, label: str) -> list[dict] | None:
    """Try each mirror in turn; return elements or None if all fail."""
    for mirror in OVERPASS_MIRRORS:
        for attempt in range(2):
            try:
                resp = requests.post(mirror, data={"data": query}, timeout=150)
                resp.raise_for_status()
                return resp.json()["elements"]
            except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
                host = mirror.split("/")[2]
                print(f"    {label}: {host} attempt {attempt + 1} failed ({e.__class__.__name__})")
                time.sleep(3)
    return None

# London bounding box (south,west,north,east) — keeps queries fast and avoids timeouts.
# DLR/Overground/Elizabeth use route=train|light_rail (NOT railway) and have no
# consistent operator/network tag, so we filter by name where needed.
_BBOX = "(51.25,-0.65,51.75,0.35)"

OVERPASS_QUERIES = {
    "tube": f'[out:json][timeout:120];\nrelation["route"="subway"]["network"="London Underground"]{_BBOX};\nout geom;',
    "dlr": f'[out:json][timeout:90];\nrelation["route"="light_rail"]["network"="Docklands Light Railway"]{_BBOX};\nout geom;',
    "overground": f'[out:json][timeout:90];\nrelation["type"="route"]["route"="train"]["name"~"Lioness|Mildmay|Windrush|Weaver|Suffragette|Liberty",i]{_BBOX};\nout geom;',
    "elizabeth": f'[out:json][timeout:90];\nrelation["type"="route"]["route"="train"]["name"~"Elizabeth line",i]{_BBOX};\nout geom;',
}

def fetch_lines() -> list[dict]:
    print("Fetching TfL line routes from Overpass API …")
    all_elements: list[dict] = []
    failed: list[str] = []
    for network, query in OVERPASS_QUERIES.items():
        print(f"  Fetching {network} …")
        els = overpass_fetch(query, network)
        if els is None:
            print(f"  ✗ {network}: all mirrors failed — skipping")
            failed.append(network)
            continue
        all_elements.extend(els)

    if failed:
        print(f"\n  WARNING: no data for {', '.join(failed)} (Overpass mirrors unavailable)")

    data = {"elements": all_elements}

    # Each route relation is one direction of one line.
    # Group way geometry by line name so each line becomes one MultiLineString.
    line_coords: dict[str, list[list[list[float]]]] = defaultdict(list)
    line_colour: dict[str, str] = {}

    for el in data["elements"]:
        if el["type"] != "relation":
            continue
        tags = el.get("tags", {})
        route_type = tags.get("route")
        if route_type not in ("subway", "light_rail", "railway", "train"):
            continue

        # Derive a canonical line name (strip direction/branch suffixes)
        name = _canonical_name(tags)
        if not name:
            continue

        # Normalize to "Foo line" (e.g. "Central Line" → "Central line")
        if name.endswith(" Line"):
            name = name[:-5] + " line"
        if name not in line_colour:
            line_colour[name] = colour_for(name, tags.get("colour"))

        for member in el.get("members", []):
            if member.get("type") == "way" and "geometry" in member:
                coords = [[g["lon"], g["lat"]] for g in member["geometry"]]
                if len(coords) >= 2:
                    line_coords[name].append(coords)

    features = []
    for name, coords_list in sorted(line_coords.items()):
        colour = line_colour[name]
        features.append({
            "type": "Feature",
            "properties": {"name": name, "color": colour},
            "geometry": {"type": "MultiLineString", "coordinates": coords_list},
        })
        print(f"  ✓ {name} ({colour}) — {len(coords_list)} segments")

    return features


def _canonical_name(tags: dict) -> str:
    """Return the line name, stripping the route suffix ': origin → destination'."""
    name = tags.get("name", "").strip()
    if not name:
        return ""
    # OSM route names are "Bakerloo line: Elephant & Castle → Harrow & Wealdstone"
    # Strip everything from ": " onwards to get just "Bakerloo line"
    if ": " in name:
        name = name[: name.index(": ")]
    # Strip parenthetical suffixes e.g. "Northern line (Bank branch)"
    if " (" in name:
        name = name[: name.index(" (")]
    return name.strip()


# ---------------------------------------------------------------------------
# 2. Fetch stations from TfL ArcGIS Open Data
# ---------------------------------------------------------------------------
# Dataset: "TfL - Stations" (item 5dcb79b6817b4bf89732de68a0337312)
# ArcGIS Open Data GeoJSON download endpoint
ARCGIS_BASE = (
    "https://services1.arcgis.com/YswvgzOodUvqkoCN/arcgis/rest/services/"
    "TfL_stations/FeatureServer/{layer}/query"
    "?where=1%3D1&outFields=NAME,LINES,NETWORK,FULL_NAME&outSR=4326&f=json"
)
# layer id → network label
STATION_LAYERS = {1: "tube", 4: "dlr", 12: "elizabeth", 22: "overground"}

def fetch_stations() -> list[dict]:
    print("\nFetching TfL stations from ArcGIS Open Data …")
    seen: set[str] = set()
    features = []

    for layer_id, network in STATION_LAYERS.items():
        url = ARCGIS_BASE.format(layer=layer_id)
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        count = 0
        for feat in data.get("features", []):
            attrs = feat.get("attributes", {})
            geo = feat.get("geometry")
            if not geo:
                continue
            name = (attrs.get("NAME") or attrs.get("FULL_NAME") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            lines = attrs.get("LINES") or attrs.get("NETWORK") or network
            features.append({
                "type": "Feature",
                "properties": {"name": name, "network": network, "lines": lines},
                "geometry": {"type": "Point", "coordinates": [geo["x"], geo["y"]]},
            })
            count += 1
        print(f"  ✓ {count} {network} stations")

    print(f"  Total: {len(features)} stations")
    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    line_features = fetch_lines()
    station_features = fetch_stations()

    lines_geojson = {"type": "FeatureCollection", "features": line_features}
    stations_geojson = {"type": "FeatureCollection", "features": station_features}

    lines_path = OUT_DIR / "tfl-lines.geojson"
    stations_path = OUT_DIR / "tfl-stations.geojson"

    # Safeguard: don't clobber good existing data with a partial/failed fetch.
    if len(line_features) < 8 and lines_path.exists():
        print(
            f"\nABORT: only got {len(line_features)} lines (expected ≥8). "
            f"Keeping existing {lines_path.name} untouched. "
            "Re-run later when Overpass mirrors recover."
        )
        sys.exit(1)

    lines_path.write_text(json.dumps(lines_geojson, separators=(",", ":")))
    stations_path.write_text(json.dumps(stations_geojson, separators=(",", ":")))

    print(f"\nWrote {len(line_features)} lines  → {lines_path}")
    print(f"Wrote {len(station_features)} stations → {stations_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
