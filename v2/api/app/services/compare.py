"""Orchestrate per-origin comparison: journey + commute cost + rent + council tax."""
from __future__ import annotations

from app.schemas import (
    CompareRequest,
    CompareResponse,
    CostBreakdown,
    JourneyResult,
    OriginResult,
)
from app.services.living_cost import get_living_cost_service
from app.services.postcode import get_postcode_service
from app.services.tfl import fan_out_journeys


WEEKS_PER_MONTH = 4.33


def _monthly_commute(single_fare: float | None, days_per_week: int) -> float:
    if not single_fare:
        return 0.0
    daily = single_fare * 2  # return journey
    return round(daily * days_per_week * WEEKS_PER_MONTH, 2)


async def run_compare(req: CompareRequest) -> CompareResponse:
    postcodes = get_postcode_service()
    living = get_living_cost_service()

    origin_postcodes = [o.postcode for o in req.origins]

    journeys = await fan_out_journeys(
        req.destination,
        origin_postcodes,
        time_bucket=req.prefs.time_bucket,
        modes=req.prefs.modes,
        journey_preference=req.prefs.journey_preference,
    )

    results: list[OriginResult] = []
    for origin, j in zip(req.origins, journeys):
        info = postcodes.lookup(origin.postcode)
        borough_name = info["borough_name"] if info else None
        borough_code = info["borough_code"] if info else None

        # Per-origin band override falls back to global prefs default.
        band = origin.council_tax_band or req.prefs.council_tax_band

        # Rent + council tax depend only on borough, so we compute them even
        # when the TfL journey lookup fails — partial info is still useful.
        ct_monthly = (
            living.council_tax_monthly(borough_code, band) if borough_code else None
        ) or 0.0
        rent_info = (
            living.rent_monthly(borough_name, req.prefs.bedroom_category) if borough_name else None
        )
        rent_median = rent_info["median"] if rent_info else None

        journey_err = j.get("error")
        single_fare = j.get("single_fare_gbp")
        duration = j.get("duration_minutes")
        monthly_commute = _monthly_commute(single_fare, req.prefs.days_per_week)
        total = round(monthly_commute + (rent_median or 0.0) + ct_monthly, 2)

        results.append(
            OriginResult(
                origin=origin.postcode,
                borough_name=borough_name,
                journey=JourneyResult(
                    duration_minutes=duration,
                    single_fare_gbp=single_fare,
                    legs=j.get("legs"),
                    steps=j.get("steps") or [],
                ),
                cost=CostBreakdown(
                    monthly_commute_gbp=monthly_commute,
                    monthly_rent_gbp=rent_median,
                    monthly_council_tax_gbp=ct_monthly,
                    monthly_total_gbp=total,
                ),
                rent_quartiles=rent_info,
                error=journey_err,
            )
        )

    return CompareResponse(destination=req.destination, results=results)
