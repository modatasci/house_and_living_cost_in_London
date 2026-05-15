import { useEffect, useState } from "react";
import { ChevronDown, Route, RotateCcw, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { JourneyDetails } from "@/components/journey-details";
import { cn, formatGBP, formatMinutes } from "@/lib/utils";
import type { CouncilTaxBand, OriginResult } from "@/types/api";

export const HOME_COLORS = ["#2563eb", "#9333ea", "#db2777", "#ea580c", "#ca8a04"];
const BANDS: CouncilTaxBand[] = ["A", "B", "C", "D", "E", "F", "G", "H"];

export function HomeResultCard({
  index,
  postcode,
  fallbackBorough,
  band,
  defaultBand,
  rentOverride,
  result,
  pareto,
  onRemove,
  onBandChange,
  onRentChange,
}: {
  index: number;
  postcode: string;
  fallbackBorough: string | null;
  band: CouncilTaxBand | null;
  defaultBand: CouncilTaxBand;
  rentOverride: number | null;
  result: OriginResult | undefined;
  pareto?: boolean;
  onRemove: () => void;
  onBandChange: (band: CouncilTaxBand | null) => void;
  onRentChange: (rent: number | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const borough = result?.borough_name ?? fallbackBorough;
  const hasSteps = !!result?.journey.steps?.length;
  const color = HOME_COLORS[index % HOME_COLORS.length];

  const medianRent = result?.cost.monthly_rent_gbp ?? null;
  const effectiveRent = rentOverride ?? medianRent;
  const baseWithoutRent = result
    ? result.cost.monthly_total_gbp - (medianRent ?? 0)
    : 0;
  const effectiveTotal = baseWithoutRent + (effectiveRent ?? 0);

  return (
    <div
      className={cn(
        "flex flex-col rounded-xl border bg-card p-3 text-sm shadow-sm transition-shadow",
        pareto && "ring-1 ring-primary/40"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-medium">
            <span
              className="inline-flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold text-white"
              style={{ background: color }}
            >
              {index + 1}
            </span>
            <span className="truncate">{postcode}</span>
            {pareto && (
              <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                Best value
              </span>
            )}
          </div>
          {borough && (
            <div className="mt-0.5 truncate text-xs text-muted-foreground">{borough}</div>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          onClick={onRemove}
          aria-label={`Remove home ${index + 1}`}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      {result && (
        <>
          <div className="mt-3 flex items-end justify-between gap-2 border-t pt-3">
            <div>
              <div className="text-[11px] text-muted-foreground">Total / month</div>
              <div className="text-xl font-semibold tabular-nums">
                {formatGBP(effectiveTotal)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[11px] text-muted-foreground">Commute</div>
              <div className="font-medium tabular-nums">
                {result.journey.duration_minutes != null
                  ? formatMinutes(result.journey.duration_minutes)
                  : "—"}
              </div>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
            <RentField
              index={index}
              median={medianRent}
              override={rentOverride}
              onChange={onRentChange}
            />
            <Stat label="Commute fare" value={`${formatGBP(result.cost.monthly_commute_gbp)}/mo`} />
            <Stat
              label="Council tax"
              value={`${formatGBP(result.cost.monthly_council_tax_gbp)}/mo`}
            />
            <label className="flex items-center justify-between gap-1.5">
              <span className="text-muted-foreground">Band</span>
              <Select
                className="h-7 w-[88px] py-0 text-[11px]"
                value={band ?? defaultBand}
                onChange={(e) => {
                  const v = e.target.value as CouncilTaxBand;
                  onBandChange(v === defaultBand ? null : v);
                }}
                aria-label={`Council tax band for home ${index + 1}`}
              >
                {BANDS.map((b) => (
                  <option key={b} value={b}>
                    {b}
                    {b === defaultBand ? " (default)" : ""}
                  </option>
                ))}
              </Select>
            </label>
            <div className="col-span-2 flex items-baseline justify-between gap-2 text-muted-foreground/60">
              <span>Energy bill est.</span>
              <span className="tabular-nums italic">coming soon</span>
            </div>
          </div>
        </>
      )}

      {result?.error && (
        <div className="mt-2 rounded-md bg-destructive/10 px-2 py-1 text-[11px] text-destructive">
          {result.error}
        </div>
      )}

      {hasSteps && (
        <div className="mt-3 border-t pt-2">
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            className="flex w-full items-center justify-between gap-2 text-[11px] font-medium text-foreground/80 hover:text-foreground"
            aria-expanded={open}
          >
            <span className="flex items-center gap-1.5">
              <Route className="h-3.5 w-3.5 text-primary" />
              View journey ({result!.journey.legs} leg
              {result!.journey.legs === 1 ? "" : "s"})
            </span>
            <ChevronDown
              className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")}
            />
          </button>
          {open && (
            <div className="mt-2">
              <JourneyDetails steps={result!.journey.steps} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RentField({
  index,
  median,
  override,
  onChange,
}: {
  index: number;
  median: number | null;
  override: number | null;
  onChange: (rent: number | null) => void;
}) {
  const [draft, setDraft] = useState(override != null ? String(Math.round(override)) : "");

  // Keep draft in sync when the override changes elsewhere (URL hydrate, reset).
  useEffect(() => {
    setDraft(override != null ? String(Math.round(override)) : "");
  }, [override]);

  const commit = () => {
    const trimmed = draft.trim();
    if (trimmed === "") {
      onChange(null);
      return;
    }
    const n = Number(trimmed);
    if (!Number.isFinite(n) || n <= 0) {
      setDraft(override != null ? String(Math.round(override)) : "");
      return;
    }
    onChange(median != null && Math.round(n) === Math.round(median) ? null : Math.round(n));
  };

  const placeholder = median != null ? String(Math.round(median)) : "—";

  return (
    <div className="flex items-center justify-between gap-1.5">
      <span className="text-muted-foreground">
        Rent{override == null && median != null ? " (median)" : ""}
      </span>
      <div className="flex items-center gap-1">
        {override != null && (
          <button
            type="button"
            onClick={() => onChange(null)}
            className="text-muted-foreground hover:text-foreground"
            aria-label={`Reset rent for home ${index + 1} to median`}
            title="Reset to median"
          >
            <RotateCcw className="h-3 w-3" />
          </button>
        )}
        <span className="text-muted-foreground">£</span>
        <input
          type="number"
          inputMode="numeric"
          min={0}
          value={draft}
          placeholder={placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          }}
          className="h-7 w-[68px] rounded-md border border-input bg-background px-1.5 text-right text-[11px] tabular-nums focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label={`Monthly rent for home ${index + 1}`}
        />
        <span className="text-muted-foreground">/mo</span>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}
