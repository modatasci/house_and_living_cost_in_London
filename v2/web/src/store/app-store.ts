import { create } from "zustand";
import type { CouncilTaxBand, Preferences } from "@/types/api";

export interface Location {
  id: string;          // stable id (postcode-normalized)
  postcode: string;    // display postcode "SW1A 1AA"
  lat: number;
  lng: number;
  borough_name: string | null;
  council_tax_band?: CouncilTaxBand | null; // per-origin override
  rent_override?: number | null;            // per-origin monthly rent override
}

export type Mode = "office" | "home" | "view";

interface AppState {
  destination: Location | null;
  origins: Location[];
  mode: Mode;
  prefs: Preferences;
  hydratedFromUrl: boolean;

  setDestination: (loc: Location | null) => void;
  addOrigin: (loc: Location) => void;
  removeOrigin: (id: string) => void;
  setOriginBand: (id: string, band: CouncilTaxBand | null) => void;
  setOriginRent: (id: string, rent: number | null) => void;
  setMode: (m: Mode) => void;
  setPrefs: (p: Partial<Preferences>) => void;
  hydrateFromUrl: () => void;
}

const DEFAULT_PREFS: Preferences = {
  days_per_week: 5,
  time_bucket: "rush",
  modes: null,
  journey_preference: "leasttime",
  bedroom_category: "One Bedroom",
  council_tax_band: "D",
};

const MAX_ORIGINS = 5;

function locId(postcode: string): string {
  return postcode.replace(/\s+/g, "").toUpperCase();
}

// --- URL sync ---

interface UrlLocation {
  postcode: string;
  lat: number;
  lng: number;
  council_tax_band?: CouncilTaxBand | null;
  rent_override?: number | null;
}

interface UrlState {
  destination: UrlLocation | null;
  origins: UrlLocation[];
  prefs: Partial<Preferences>;
}

function encodeLocations(locs: UrlLocation[]): string {
  // Format per loc: `pcds|lat,lng[|band[|rent]]` — trailing empty parts trimmed.
  return locs
    .map((l) => {
      const parts = [
        l.postcode,
        `${l.lat.toFixed(5)},${l.lng.toFixed(5)}`,
        l.council_tax_band ?? "",
        l.rent_override != null ? String(Math.round(l.rent_override)) : "",
      ];
      while (parts.length > 2 && parts[parts.length - 1] === "") parts.pop();
      return parts.join("|");
    })
    .join(";");
}

function decodeLocations(raw: string | null): UrlLocation[] {
  if (!raw) return [];
  return raw
    .split(";")
    .map((s) => {
      const parts = s.split("|");
      if (parts.length < 2) return null;
      const [postcode, latlng, bandRaw, rentRaw] = parts;
      const [lat, lng] = latlng.split(",").map(Number);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
      const band = bandRaw && /^[A-H]$/.test(bandRaw) ? (bandRaw as CouncilTaxBand) : undefined;
      const rentNum = rentRaw ? Number(rentRaw) : NaN;
      const rent_override = Number.isFinite(rentNum) && rentNum > 0 ? rentNum : undefined;
      return { postcode, lat, lng, council_tax_band: band, rent_override };
    })
    .filter((x): x is NonNullable<typeof x> => x !== null);
}

function readUrl(): UrlState {
  const p = new URLSearchParams(window.location.search);
  const destRaw = p.get("o");
  const dest = decodeLocations(destRaw)[0] ?? null;
  const prefs: Partial<Preferences> = {};
  if (p.has("d")) {
    const n = Number(p.get("d"));
    if (Number.isFinite(n) && n >= 1 && n <= 7) prefs.days_per_week = n;
  }
  if (p.has("b")) {
    const v = p.get("b") ?? "";
    if (/^[A-H]$/.test(v)) prefs.council_tax_band = v as Preferences["council_tax_band"];
  }
  if (p.has("br")) {
    const v = p.get("br") ?? "";
    const valid: Preferences["bedroom_category"][] = [
      "Room",
      "Studio",
      "One Bedroom",
      "Two Bedrooms",
      "Three Bedrooms",
      "Four or More Bedrooms",
    ];
    if ((valid as string[]).includes(v)) {
      prefs.bedroom_category = v as Preferences["bedroom_category"];
    }
  }
  if (p.has("t")) {
    const v = p.get("t") ?? "";
    if (v === "rush" || v === "off_peak" || v === "now") {
      prefs.time_bucket = v;
    }
  }
  return { destination: dest, origins: decodeLocations(p.get("h")), prefs };
}

function writeUrl(state: { destination: Location | null; origins: Location[]; prefs: Preferences }) {
  const p = new URLSearchParams();
  if (state.destination) p.set("o", encodeLocations([state.destination]));
  if (state.origins.length) p.set("h", encodeLocations(state.origins));
  if (state.prefs.days_per_week !== DEFAULT_PREFS.days_per_week)
    p.set("d", String(state.prefs.days_per_week));
  if (state.prefs.council_tax_band !== DEFAULT_PREFS.council_tax_band)
    p.set("b", state.prefs.council_tax_band);
  if (state.prefs.bedroom_category !== DEFAULT_PREFS.bedroom_category)
    p.set("br", state.prefs.bedroom_category);
  if (state.prefs.time_bucket !== DEFAULT_PREFS.time_bucket)
    p.set("t", state.prefs.time_bucket);
  const qs = p.toString();
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  window.history.replaceState(null, "", url);
}

export const useAppStore = create<AppState>((set, get) => ({
  destination: null,
  origins: [],
  mode: "office",
  prefs: DEFAULT_PREFS,
  hydratedFromUrl: false,

  setDestination: (loc) => {
    set({ destination: loc, mode: loc ? "home" : "office" });
    const s = get();
    writeUrl({ destination: s.destination, origins: s.origins, prefs: s.prefs });
  },

  addOrigin: (loc) => {
    const { origins } = get();
    if (origins.some((o) => o.id === loc.id)) return;
    const next = [...origins, loc].slice(0, MAX_ORIGINS);
    set({ origins: next });
    const s = get();
    writeUrl({ destination: s.destination, origins: s.origins, prefs: s.prefs });
  },

  removeOrigin: (id) => {
    set({ origins: get().origins.filter((o) => o.id !== id) });
    const s = get();
    writeUrl({ destination: s.destination, origins: s.origins, prefs: s.prefs });
  },

  setOriginBand: (id, band) => {
    set({
      origins: get().origins.map((o) =>
        o.id === id ? { ...o, council_tax_band: band ?? undefined } : o
      ),
    });
    const s = get();
    writeUrl({ destination: s.destination, origins: s.origins, prefs: s.prefs });
  },

  setOriginRent: (id, rent) => {
    set({
      origins: get().origins.map((o) =>
        o.id === id ? { ...o, rent_override: rent ?? undefined } : o
      ),
    });
    const s = get();
    writeUrl({ destination: s.destination, origins: s.origins, prefs: s.prefs });
  },

  setMode: (m) => set({ mode: m }),

  setPrefs: (p) => {
    set({ prefs: { ...get().prefs, ...p } });
    const s = get();
    writeUrl({ destination: s.destination, origins: s.origins, prefs: s.prefs });
  },

  hydrateFromUrl: () => {
    if (get().hydratedFromUrl) return;
    const url = readUrl();
    const dest = url.destination
      ? {
          id: locId(url.destination.postcode),
          postcode: url.destination.postcode,
          lat: url.destination.lat,
          lng: url.destination.lng,
          borough_name: null,
        }
      : null;
    const origins = url.origins.map((o) => ({
      id: locId(o.postcode),
      postcode: o.postcode,
      lat: o.lat,
      lng: o.lng,
      borough_name: null,
      council_tax_band: o.council_tax_band,
      rent_override: o.rent_override,
    }));
    set({
      destination: dest,
      origins,
      mode: dest ? "home" : "office",
      prefs: { ...DEFAULT_PREFS, ...url.prefs } as Preferences,
      hydratedFromUrl: true,
    });
  },
}));

export { locId, MAX_ORIGINS, DEFAULT_PREFS };
