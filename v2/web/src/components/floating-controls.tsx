import { useState } from "react";
import { Briefcase, ChevronUp, Hand, Home as HomeIcon, MapPin, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Segmented } from "@/components/ui/segmented";
import { PostcodeInput } from "@/components/postcode-input";
import { HOME_COLORS } from "@/components/home-result-card";
import { useAppStore, MAX_ORIGINS, type Mode } from "@/store/app-store";

const MODE_OPTIONS: { value: Mode; label: string; icon: React.ReactNode }[] = [
  { value: "office", label: "Office", icon: <Briefcase className="h-3.5 w-3.5" /> },
  { value: "home", label: "Home", icon: <HomeIcon className="h-3.5 w-3.5" /> },
  { value: "view", label: "View", icon: <Hand className="h-3.5 w-3.5" /> },
];

export function FloatingControls() {
  const destination = useAppStore((s) => s.destination);
  const origins = useAppStore((s) => s.origins);
  const mode = useAppStore((s) => s.mode);
  const setMode = useAppStore((s) => s.setMode);
  const setDestination = useAppStore((s) => s.setDestination);
  const addOrigin = useAppStore((s) => s.addOrigin);
  const removeOrigin = useAppStore((s) => s.removeOrigin);

  const [collapsed, setCollapsed] = useState(false);
  const homesFull = origins.length >= MAX_ORIGINS;

  if (collapsed) {
    const count = (destination ? 1 : 0) + origins.length;
    return (
      <div className="pointer-events-none absolute inset-x-0 top-4 z-20 flex justify-center px-4">
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="pointer-events-auto flex items-center gap-2 rounded-full border bg-background/80 px-4 py-2 text-sm font-medium shadow-xl backdrop-blur-md transition-colors hover:bg-background"
        >
          <MapPin className="h-4 w-4 text-primary" />
          Locations
          {count > 0 && (
            <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[11px] tabular-nums text-muted-foreground">
              {count}
            </span>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="pointer-events-none absolute inset-x-0 top-4 z-20 flex justify-center px-4">
      <div className="pointer-events-auto w-full max-w-md rounded-2xl border bg-background/80 p-3 shadow-xl backdrop-blur-md">
        <div className="mb-2 flex items-center gap-2">
          <div className="flex-1">
            <Segmented value={mode} onChange={setMode} options={MODE_OPTIONS} />
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            onClick={() => setCollapsed(true)}
            aria-label="Hide controls"
            title="Hide controls"
          >
            <ChevronUp className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-2">
          {/* Office */}
          {destination ? (
            <Chip
              badge="O"
              badgeColor="hsl(173 80% 36%)"
              label={destination.postcode}
              sub={destination.borough_name}
              onRemove={() => setDestination(null)}
            />
          ) : (
            <PostcodeInput
              placeholder="Set your office postcode…"
              onSelect={setDestination}
              autoFocus
            />
          )}

          {/* Home input */}
          {!homesFull && (
            <PostcodeInput
              placeholder={
                !destination
                  ? "Set an office first"
                  : origins.length === 0
                    ? "Add a home to compare…"
                    : "Add another home…"
              }
              onSelect={addOrigin}
              disabled={!destination}
            />
          )}

          {/* Compact home chips */}
          {origins.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-0.5">
              {origins.map((o, idx) => (
                <span
                  key={o.id}
                  className="inline-flex items-center gap-1.5 rounded-full border bg-card py-1 pl-1 pr-1.5 text-xs"
                >
                  <span
                    className="inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold text-white"
                    style={{ background: HOME_COLORS[idx % HOME_COLORS.length] }}
                  >
                    {idx + 1}
                  </span>
                  {o.postcode}
                  <button
                    type="button"
                    onClick={() => removeOrigin(o.id)}
                    className="ml-0.5 rounded-full p-0.5 text-muted-foreground hover:bg-secondary hover:text-foreground"
                    aria-label={`Remove home ${idx + 1}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              <span className="self-center pl-1 text-[11px] text-muted-foreground">
                {origins.length}/{MAX_ORIGINS}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Chip({
  badge,
  badgeColor,
  label,
  sub,
  onRemove,
}: {
  badge: string;
  badgeColor: string;
  label: string;
  sub: string | null;
  onRemove: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-md border bg-card px-2.5 py-2 text-sm">
      <div className="flex min-w-0 items-center gap-2">
        <span
          className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
          style={{ background: badgeColor }}
        >
          {badge}
        </span>
        <span className="truncate font-medium">{label}</span>
        {sub && <span className="truncate text-xs text-muted-foreground">· {sub}</span>}
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 shrink-0"
        onClick={onRemove}
        aria-label="Remove"
      >
        <X className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
