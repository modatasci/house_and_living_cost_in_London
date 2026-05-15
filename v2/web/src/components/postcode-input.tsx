import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { geocodePostcode } from "@/lib/geocode";
import { cn } from "@/lib/utils";
import type { Location } from "@/store/app-store";
import { locId } from "@/store/app-store";

interface Props {
  placeholder?: string;
  onSelect: (loc: Location) => void;
  disabled?: boolean;
  autoFocus?: boolean;
}

function useDebounced<T>(value: T, ms = 200): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}

export function PostcodeInput({ placeholder, onSelect, disabled, autoFocus }: Props) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounced = useDebounced(q.trim(), 180);

  const { data: hits = [], isFetching } = useQuery({
    queryKey: ["pc-search", debounced],
    queryFn: () => api.searchPostcodes(debounced, 8),
    enabled: debounced.length >= 2,
    staleTime: 5 * 60_000,
  });

  // Click-outside to close
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  async function pick(postcode: string, borough_name: string | null) {
    setResolving(true);
    setError(null);
    try {
      const geo = await geocodePostcode(postcode);
      if (!geo) {
        setError(`Couldn't locate ${postcode}. Try another postcode.`);
        return;
      }
      onSelect({
        id: locId(geo.postcode),
        postcode: geo.postcode,
        lat: geo.lat,
        lng: geo.lng,
        borough_name: borough_name ?? geo.district,
      });
      setQ("");
      setOpen(false);
    } finally {
      setResolving(false);
    }
  }

  const busy = isFetching || resolving;

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-8 pr-8"
          placeholder={placeholder ?? "Postcode e.g. SW1A 1AA"}
          value={q}
          disabled={disabled}
          autoFocus={autoFocus}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && hits[0]) {
              e.preventDefault();
              void pick(hits[0].postcode, hits[0].borough_name);
            }
            if (e.key === "Escape") setOpen(false);
          }}
        />
        {busy && (
          <Loader2 className="absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {error && <p className="mt-1 text-xs text-destructive">{error}</p>}

      {open && debounced.length >= 2 && (
        <div
          className={cn(
            "absolute z-50 mt-1 max-h-72 w-full overflow-auto rounded-md border bg-popover bg-card",
            "shadow-md"
          )}
          role="listbox"
        >
          {hits.length === 0 && !isFetching && (
            <div className="px-3 py-2 text-sm text-muted-foreground">No matches in London</div>
          )}
          {hits.map((h) => (
            <button
              key={h.postcode}
              type="button"
              role="option"
              className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm hover:bg-secondary"
              onClick={() => void pick(h.postcode, h.borough_name)}
            >
              <span className="font-medium">{h.postcode}</span>
              <span className="text-xs text-muted-foreground">{h.borough_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
