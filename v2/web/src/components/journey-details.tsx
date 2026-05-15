import { Bus, Footprints, Train, TramFront, Bike, HelpCircle } from "lucide-react";
import type { JourneyStep } from "@/types/api";
import { formatMinutes } from "@/lib/utils";

// Map TfL mode names → icon + color
const MODE_STYLE: Record<string, { color: string; Icon: typeof Bus }> = {
  tube: { color: "#003688", Icon: Train },
  bus: { color: "#DC241F", Icon: Bus },
  walking: { color: "#6b7280", Icon: Footprints },
  dlr: { color: "#00A4A7", Icon: Train },
  overground: { color: "#EE7C0E", Icon: Train },
  "elizabeth-line": { color: "#6950A1", Icon: Train },
  "national-rail": { color: "#0019A8", Icon: Train },
  tram: { color: "#66CC00", Icon: TramFront },
  cycle: { color: "#0098D4", Icon: Bike },
  "river-bus": { color: "#00AFE8", Icon: Train },
};

function styleFor(mode: string) {
  return MODE_STYLE[mode.toLowerCase()] ?? { color: "#6b7280", Icon: HelpCircle };
}

export function JourneyDetails({ steps }: { steps: JourneyStep[] }) {
  if (!steps.length) {
    return <p className="text-[11px] text-muted-foreground">No leg details from TfL.</p>;
  }
  return (
    <ol className="space-y-1.5">
      {steps.map((s, i) => {
        const { color, Icon } = styleFor(s.mode);
        return (
          <li key={i} className="flex gap-2 text-[11px] leading-tight">
            <div
              className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-white"
              style={{ background: color }}
              title={s.mode}
            >
              <Icon className="h-3 w-3" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-medium capitalize text-foreground">
                  {s.line ?? s.mode.replace("-", " ")}
                </span>
                <span className="tabular-nums text-muted-foreground">
                  {formatMinutes(s.duration_minutes)}
                </span>
              </div>
              {(s.start || s.end) && (
                <div className="truncate text-muted-foreground">
                  {s.start ?? "?"} → {s.end ?? "?"}
                </div>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
