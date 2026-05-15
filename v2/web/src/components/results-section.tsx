import { forwardRef, useState } from "react";
import { BarChart3, Download, Loader2, MapPin, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Preferences } from "@/components/preferences";
import { CostChart } from "@/components/cost-chart";
import { HomeResultCard } from "@/components/home-result-card";
import { useCompare } from "@/hooks/use-compare";
import { useAppStore, locId } from "@/store/app-store";
import { paretoFrontier } from "@/lib/pareto";
import { buildCompareCsv, downloadCsv } from "@/lib/csv";
import { cn } from "@/lib/utils";
import type { OriginResult } from "@/types/api";

export const ResultsSection = forwardRef<HTMLElement>((_props, ref) => {
  const [filtersOpen, setFiltersOpen] = useState(false);

  const destination = useAppStore((s) => s.destination);
  const origins = useAppStore((s) => s.origins);
  const prefs = useAppStore((s) => s.prefs);
  const removeOrigin = useAppStore((s) => s.removeOrigin);
  const setOriginBand = useAppStore((s) => s.setOriginBand);
  const setOriginRent = useAppStore((s) => s.setOriginRent);

  const { data, isFetching } = useCompare();

  const resultsByOrigin = new Map<string, OriginResult>();
  data?.results.forEach((r) => resultsByOrigin.set(locId(r.origin), r));

  // Pareto set keyed by origin id (only successful journeys participate)
  const paretoIds = new Set<string>();
  if (data) {
    const pts = data.results
      .filter((r) => r.journey.duration_minutes != null)
      .map((r) => ({
        id: locId(r.origin),
        time: r.journey.duration_minutes ?? 0,
        cost: r.cost.monthly_total_gbp,
      }));
    paretoFrontier(pts).forEach((p) => paretoIds.add(p.id));
  }

  const hasInputs = !!destination && origins.length > 0;

  return (
    <section ref={ref} className="border-t bg-secondary/30">
      <div className="mx-auto w-full max-w-7xl px-4 py-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Results</h2>
            <p className="text-xs text-muted-foreground">
              {hasInputs
                ? `${origins.length} home${origins.length === 1 ? "" : "s"} vs ${destination!.postcode}`
                : "Set an office and add homes above to compare"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isFetching && (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFiltersOpen((o) => !o)}
              aria-expanded={filtersOpen}
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
              Preferences
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!data}
              onClick={() =>
                data &&
                downloadCsv(
                  `compare-${destination!.postcode.replace(/\s+/g, "_")}.csv`,
                  buildCompareCsv(data)
                )
              }
            >
              <Download className="h-3.5 w-3.5" />
              CSV
            </Button>
          </div>
        </div>

        {/* Filters disclosure */}
        <div
          className={cn(
            "grid transition-all duration-200",
            filtersOpen ? "mt-4 grid-rows-[1fr]" : "grid-rows-[0fr]"
          )}
        >
          <div className="overflow-hidden">
            <Preferences />
          </div>
        </div>

        {!hasInputs ? (
          <div className="mt-6 flex flex-col items-center gap-2 rounded-xl border border-dashed bg-card/50 py-16 text-center text-muted-foreground">
            <MapPin className="h-8 w-8 opacity-40" />
            <p className="text-sm">Your comparison will appear here.</p>
          </div>
        ) : (
          <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,460px)]">
            {/* Home cards */}
            <div className="grid gap-3 sm:grid-cols-2">
              {origins.map((o, idx) => (
                <HomeResultCard
                  key={o.id}
                  index={idx}
                  postcode={o.postcode}
                  fallbackBorough={o.borough_name}
                  band={o.council_tax_band ?? null}
                  defaultBand={prefs.council_tax_band}
                  result={resultsByOrigin.get(o.id)}
                  pareto={paretoIds.has(o.id)}
                  rentOverride={o.rent_override ?? null}
                  onRemove={() => removeOrigin(o.id)}
                  onBandChange={(b) => setOriginBand(o.id, b)}
                  onRentChange={(r) => setOriginRent(o.id, r)}
                />
              ))}
            </div>

            {/* Chart */}
            <div className="rounded-xl border bg-card p-3">
              <div className="mb-1 flex items-center gap-2 px-1 text-sm font-semibold tracking-tight">
                <BarChart3 className="h-4 w-4 text-primary" />
                Cost vs commute
                <span className="ml-1 text-xs font-normal text-muted-foreground">
                  best-value homes highlighted
                </span>
              </div>
              <div className="h-[340px]">
                <CostChart />
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
});
ResultsSection.displayName = "ResultsSection";
