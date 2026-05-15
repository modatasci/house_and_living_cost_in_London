import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { type LngLatBoundsLike, type Map as MlMap, Marker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Train } from "lucide-react";

import { useTheme } from "@/components/theme-provider";
import { reverseGeocode } from "@/lib/geocode";
import { useAppStore, locId, type Location } from "@/store/app-store";

const TRANSIT_LINE_LAYER = "tfl-lines-layer";
const TRANSIT_STATION_LAYER = "tfl-stations-layer";
const TRANSIT_LAYER_IDS = [TRANSIT_LINE_LAYER, TRANSIT_STATION_LAYER];

const LONDON_BOUNDS: LngLatBoundsLike = [
  [-0.51, 51.28], // SW
  [0.33, 51.69],  // NE
];

const LIGHT_STYLE = "https://tiles.openfreemap.org/styles/positron";
const DARK_STYLE = "https://tiles.openfreemap.org/styles/dark";

function createPinElement(opts: { color: string; label: string; isOffice?: boolean }): HTMLElement {
  const el = document.createElement("div");
  el.style.cursor = "pointer";
  el.innerHTML = `
    <div style="
      display:flex;align-items:center;justify-content:center;
      width:${opts.isOffice ? "32" : "28"}px;
      height:${opts.isOffice ? "32" : "28"}px;
      border-radius:9999px;
      background:${opts.color};
      color:white;font-weight:600;font-size:13px;
      box-shadow:0 2px 6px rgba(0,0,0,.35), 0 0 0 3px rgba(255,255,255,.85);
      transform: translate(0, -50%);
    ">${opts.label}</div>
  `;
  return el;
}

// Distinct, accessible colors for home pins (avoid the office primary)
const HOME_COLORS = ["#2563eb", "#9333ea", "#db2777", "#ea580c", "#ca8a04"];

export function LondonMap() {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const markersRef = useRef<Map<string, Marker>>(new Map());
  const officeMarkerRef = useRef<Marker | null>(null);
  const [showTransit, setShowTransit] = useState(false);
  const [mapReady, setMapReady] = useState(false);

  const { theme } = useTheme();
  const isDark =
    theme === "dark" ||
    (theme === "system" &&
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  const destination = useAppStore((s) => s.destination);
  const origins = useAppStore((s) => s.origins);
  const mode = useAppStore((s) => s.mode);
  const setDestination = useAppStore((s) => s.setDestination);
  const addOrigin = useAppStore((s) => s.addOrigin);
  const [pickingAt, setPickingAt] = useState<{ lng: number; lat: number } | null>(null);
  const [pickError, setPickError] = useState<string | null>(null);

  // We read mode from a ref inside the click handler so we don't re-attach handlers on every change.
  const modeRef = useRef(mode);
  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  // Init / style swap
  useEffect(() => {
    if (!ref.current) return;
    if (mapRef.current) {
      setMapReady(false);
      mapRef.current.setStyle(isDark ? DARK_STYLE : LIGHT_STYLE);
      mapRef.current.once("styledata", () => setMapReady(true));
      return;
    }
    const map = new maplibregl.Map({
      container: ref.current,
      style: isDark ? DARK_STYLE : LIGHT_STYLE,
      center: [-0.1278, 51.5074],
      zoom: 10.5,
      maxBounds: [
        [-0.7, 51.15],
        [0.5, 51.8],
      ],
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");
    map.fitBounds(LONDON_BOUNDS, { padding: 30, duration: 0 });

    map.on("load", () => setMapReady(true));

    map.on("click", async (e) => {
      const m = modeRef.current;
      if (m === "view") {
        setPickError("Switch to 'Set office' or 'Add home' to drop a pin");
        setTimeout(() => setPickError(null), 2500);
        return;
      }
      const state = useAppStore.getState();
      if (m === "home" && state.origins.length >= 5) {
        setPickError("Maximum 5 homes — remove one first");
        setTimeout(() => setPickError(null), 2500);
        return;
      }
      setPickingAt({ lng: e.lngLat.lng, lat: e.lngLat.lat });
      setPickError(null);
      console.log("[map] click", { mode: m, lng: e.lngLat.lng, lat: e.lngLat.lat });
      try {
        const geo = await reverseGeocode(e.lngLat.lat, e.lngLat.lng);
        console.log("[map] reverseGeocode result", geo);
        if (!geo) {
          setPickError("No nearby UK postcode found — try clicking closer to a road");
          setTimeout(() => setPickError(null), 4000);
          return;
        }
        const loc: Location = {
          id: locId(geo.postcode),
          postcode: geo.postcode,
          lat: geo.lat,
          lng: geo.lng,
          borough_name: geo.district,
        };
        if (m === "office") setDestination(loc);
        else addOrigin(loc);
      } catch (err) {
        console.error("[map] reverseGeocode failed", err);
        setPickError("Could not reach geocoding service — check your network");
        setTimeout(() => setPickError(null), 4000);
      } finally {
        setPickingAt(null);
      }
    });

    mapRef.current = map;

    // Resize on container resize (handles initial height-0 → real height transition)
    const ro = new ResizeObserver(() => map.resize());
    if (ref.current) ro.observe(ref.current);

    return () => {
      ro.disconnect();
      map.remove();
      mapRef.current = null;
    };
    // We intentionally only depend on theme; click handler reads modeRef.current.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDark]);

  // Office marker
  useEffect(() => {
    if (!mapRef.current) return;
    officeMarkerRef.current?.remove();
    officeMarkerRef.current = null;
    if (destination) {
      const el = createPinElement({ color: "hsl(173 80% 36%)", label: "O", isOffice: true });
      el.title = `Office: ${destination.postcode}`;
      officeMarkerRef.current = new maplibregl.Marker({ element: el })
        .setLngLat([destination.lng, destination.lat])
        .addTo(mapRef.current);
    }
  }, [destination]);

  // Home markers (additive: only add/remove diffs to avoid flicker)
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;
    const seen = new Set<string>();
    origins.forEach((o, idx) => {
      seen.add(o.id);
      const existing = markersRef.current.get(o.id);
      if (existing) return;
      const color = HOME_COLORS[idx % HOME_COLORS.length];
      const el = createPinElement({ color, label: String(idx + 1) });
      el.title = `Home ${idx + 1}: ${o.postcode}`;
      const marker = new maplibregl.Marker({ element: el }).setLngLat([o.lng, o.lat]).addTo(map);
      markersRef.current.set(o.id, marker);
    });
    // Remove markers no longer in the store
    for (const [id, marker] of markersRef.current) {
      if (!seen.has(id)) {
        marker.remove();
        markersRef.current.delete(id);
      }
    }
  }, [origins]);

  // Fit bounds when destination + origins are set
  useEffect(() => {
    if (!mapRef.current) return;
    const pts: [number, number][] = [];
    if (destination) pts.push([destination.lng, destination.lat]);
    origins.forEach((o) => pts.push([o.lng, o.lat]));
    if (pts.length < 2) return;
    const b = new maplibregl.LngLatBounds(pts[0], pts[0]);
    pts.forEach((p) => b.extend(p));
    mapRef.current.fitBounds(b, { padding: 60, maxZoom: 13, duration: 600 });
  }, [destination, origins]);

  // Cursor + crosshair feedback per mode
  useEffect(() => {
    if (!mapRef.current) return;
    const canvas = mapRef.current.getCanvas();
    canvas.style.cursor = mode === "view" ? "" : "crosshair";
  }, [mode]);

  // Transit overlay — bundled GeoJSON from /tfl-lines.geojson + /tfl-stations.geojson
  const transitDataRef = useRef<{ lines: unknown; stations: unknown } | null>(null);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    if (!showTransit) {
      for (const id of TRANSIT_LAYER_IDS) {
        if (map.getLayer(id)) map.removeLayer(id);
      }
      if (map.getSource("tfl-lines")) map.removeSource("tfl-lines");
      if (map.getSource("tfl-stations")) map.removeSource("tfl-stations");
      return;
    }

    async function addLayers() {
      if (!transitDataRef.current) {
        const [linesRes, stationsRes] = await Promise.all([
          fetch("/tfl-lines.geojson"),
          fetch("/tfl-stations.geojson"),
        ]);
        transitDataRef.current = {
          lines: await linesRes.json(),
          stations: await stationsRes.json(),
        };
      }
      const map = mapRef.current;
      if (!map) return;
      const { lines, stations } = transitDataRef.current!;

      if (!map.getSource("tfl-lines")) {
        map.addSource("tfl-lines", { type: "geojson", data: lines as never });
      }
      if (!map.getSource("tfl-stations")) {
        map.addSource("tfl-stations", { type: "geojson", data: stations as never });
      }

      if (!map.getLayer(TRANSIT_LINE_LAYER)) {
        map.addLayer({
          id: TRANSIT_LINE_LAYER,
          type: "line",
          source: "tfl-lines",
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": ["get", "color"],
            "line-width": ["interpolate", ["linear"], ["zoom"], 8, 1.5, 12, 2.5, 15, 4],
            "line-opacity": 0.9,
          },
        });
      }

      if (!map.getLayer(TRANSIT_STATION_LAYER)) {
        map.addLayer({
          id: TRANSIT_STATION_LAYER,
          type: "circle",
          source: "tfl-stations",
          minzoom: 10,
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 2, 14, 4],
            "circle-color": "#ffffff",
            "circle-stroke-width": 1.5,
            "circle-stroke-color": "#555555",
          },
        });
      }
    }

    addLayers();
  }, [showTransit, mapReady]);

  const modeLabel = useMemo(() => {
    if (mode === "office") return "Click anywhere to set your office";
    if (mode === "home") return "Click to add a home to compare";
    return "Pan / zoom — picking disabled";
  }, [mode]);

  return (
    <div className="relative h-full w-full">
      <div ref={ref} className="h-full w-full" />
      <div className="pointer-events-none absolute left-3 top-3 rounded-md bg-background/90 px-2.5 py-1.5 text-xs font-medium shadow-sm backdrop-blur">
        {modeLabel}
      </div>
      {pickingAt && (
        <div className="pointer-events-none absolute bottom-3 left-1/2 -translate-x-1/2 rounded-md bg-background/95 px-3 py-1.5 text-xs shadow-md">
          Resolving postcode…
        </div>
      )}
      {pickError && (
        <div className="pointer-events-none absolute bottom-3 left-1/2 -translate-x-1/2 rounded-md bg-destructive px-3 py-1.5 text-xs text-destructive-foreground shadow-md">
          {pickError}
        </div>
      )}
      <button
        type="button"
        onClick={() => setShowTransit((v) => !v)}
        className={`absolute bottom-4 left-4 z-10 flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium shadow-md backdrop-blur transition-colors ${
          showTransit
            ? "bg-primary text-primary-foreground border-primary"
            : "bg-background/80 hover:bg-background"
        }`}
      >
        <Train className="h-3.5 w-3.5" />
        {showTransit ? "Hide transit" : "Show transit"}
      </button>
    </div>
  );
}
