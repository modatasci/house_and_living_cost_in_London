import { ChevronDown, Settings2 } from "lucide-react";
import { useState } from "react";
import { Select } from "@/components/ui/select";
import { useAppStore } from "@/store/app-store";
import { cn } from "@/lib/utils";

const BANDS = ["A", "B", "C", "D", "E", "F", "G", "H"] as const;
const BEDROOMS = [
  "Room",
  "Studio",
  "One Bedroom",
  "Two Bedrooms",
  "Three Bedrooms",
  "Four or More Bedrooms",
] as const;
const TIME_BUCKETS = [
  { value: "rush", label: "Rush hour (08:30)" },
  { value: "off_peak", label: "Off-peak (11:00)" },
  { value: "now", label: "Now" },
] as const;
const JOURNEY_PREFS = [
  { value: "leasttime", label: "Least time" },
  { value: "leastinterchange", label: "Fewest changes" },
  { value: "leastwalking", label: "Least walking" },
] as const;

export function Preferences() {
  const [open, setOpen] = useState(true);
  const prefs = useAppStore((s) => s.prefs);
  const setPrefs = useAppStore((s) => s.setPrefs);

  return (
    <div className="rounded-lg border bg-card">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
      >
        <span className="flex items-center gap-2 text-sm font-semibold tracking-tight">
          <Settings2 className="h-4 w-4 text-primary" /> Preferences
        </span>
        <ChevronDown
          className={cn("h-4 w-4 text-muted-foreground transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <div className="grid grid-cols-2 gap-2 border-t px-4 py-3">
          <Field label="Days per week">
            <Select
              value={prefs.days_per_week}
              onChange={(e) => setPrefs({ days_per_week: Number(e.target.value) })}
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} day{n === 1 ? "" : "s"}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Departure">
            <Select
              value={prefs.time_bucket}
              onChange={(e) =>
                setPrefs({ time_bucket: e.target.value as typeof prefs.time_bucket })
              }
            >
              {TIME_BUCKETS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Bedrooms">
            <Select
              value={prefs.bedroom_category}
              onChange={(e) =>
                setPrefs({ bedroom_category: e.target.value as typeof prefs.bedroom_category })
              }
            >
              {BEDROOMS.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Council tax band">
            <Select
              value={prefs.council_tax_band}
              onChange={(e) =>
                setPrefs({ council_tax_band: e.target.value as typeof prefs.council_tax_band })
              }
            >
              {BANDS.map((b) => (
                <option key={b} value={b}>
                  Band {b}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Route preference" full>
            <Select
              value={prefs.journey_preference}
              onChange={(e) =>
                setPrefs({
                  journey_preference: e.target.value as typeof prefs.journey_preference,
                })
              }
            >
              {JOURNEY_PREFS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  children,
  full,
}: {
  label: string;
  children: React.ReactNode;
  full?: boolean;
}) {
  return (
    <label className={cn("flex flex-col gap-1 text-[11px] text-muted-foreground", full && "col-span-2")}>
      {label}
      {children}
    </label>
  );
}
