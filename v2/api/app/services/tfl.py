"""
Async TfL Journey Planner client.

Adapted from src/route_calculator.py (sync, requests-based) to httpx async,
suitable for parallel fan-out over multiple origins.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
import asyncio
import httpx

from app.config import settings


TFL_BASE = "https://api.tfl.gov.uk"

# Time bucket -> (HHmm, time_is_arrival)
TIME_BUCKETS: dict[str, tuple[str | None, bool]] = {
    "rush": ("0830", False),
    "off_peak": ("1100", False),
    "now": (None, False),
}


def _extract_fare(journey: dict[str, Any]) -> float | None:
    """Return single-fare in GBP, or None if unavailable."""
    fare = journey.get("fare") or {}
    total = fare.get("totalCost")
    if total:
        return round(total / 100, 2)
    fares = fare.get("fares") or []
    if fares:
        first = fares[0]
        for key in ("lowZone", "highZone"):
            val = first.get(key)
            if val:
                return round(val / 100, 2)
    return None


def _extract_steps(journey: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one entry per leg with mode, endpoints, duration, route name, summary."""
    out: list[dict[str, Any]] = []
    for leg in journey.get("legs") or []:
        mode = (leg.get("mode") or {}).get("name") or "unknown"
        dep = leg.get("departurePoint") or {}
        arr = leg.get("arrivalPoint") or {}
        instruction = leg.get("instruction") or {}
        route_options = leg.get("routeOptions") or []
        line = next(
            (opt.get("name") for opt in route_options if opt.get("name")),
            None,
        )
        out.append(
            {
                "mode": mode,
                "start": dep.get("commonName"),
                "end": arr.get("commonName"),
                "duration_minutes": leg.get("duration"),
                "line": line,
                "summary": instruction.get("summary"),
            }
        )
    return out


class TfLClient:
    def __init__(self, app_key: str | None, client: httpx.AsyncClient):
        self.app_key = app_key
        self.client = client

    async def journey(
        self,
        from_pc: str,
        to_pc: str,
        *,
        time_bucket: str = "rush",
        modes: list[str] | None = None,
        journey_preference: str = "leasttime",
    ) -> dict[str, Any]:
        """Return {duration_minutes, single_fare_gbp, legs, error?}."""
        if not self.app_key:
            return {"error": "TFL_APP_KEY not configured"}

        time_str, time_is_arrival = TIME_BUCKETS.get(time_bucket, TIME_BUCKETS["rush"])
        url = f"{TFL_BASE}/Journey/JourneyResults/{from_pc.replace(' ', '%20')}/to/{to_pc.replace(' ', '%20')}"
        params: dict[str, Any] = {
            "app_key": self.app_key,
            "timeIs": "Arriving" if time_is_arrival else "Departing",
            "date": datetime.now().strftime("%Y%m%d"),
            "journeyPreference": journey_preference,
        }
        if time_str:
            params["time"] = time_str
        if modes:
            params["mode"] = ",".join(modes)

        try:
            r = await self.client.get(url, params=params, timeout=15.0)
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPError as e:
            return {"error": f"TfL request failed: {e}"}

        journeys = data.get("journeys") or []
        if not journeys:
            return {"error": "No journey found"}

        j = journeys[0]
        return {
            "duration_minutes": j.get("duration"),
            "single_fare_gbp": _extract_fare(j),
            "legs": len(j.get("legs") or []),
            "steps": _extract_steps(j),
        }


async def fan_out_journeys(
    destination: str,
    origins: list[str],
    *,
    time_bucket: str,
    modes: list[str] | None,
    journey_preference: str,
) -> list[dict[str, Any]]:
    """Run TfL queries for all origins in parallel."""
    async with httpx.AsyncClient() as client:
        tfl = TfLClient(settings.tfl_app_key, client)
        coros = [
            tfl.journey(
                o,
                destination,
                time_bucket=time_bucket,
                modes=modes,
                journey_preference=journey_preference,
            )
            for o in origins
        ]
        return await asyncio.gather(*coros)
