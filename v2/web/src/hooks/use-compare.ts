import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAppStore } from "@/store/app-store";

export function useCompare() {
  const destination = useAppStore((s) => s.destination);
  const origins = useAppStore((s) => s.origins);
  const prefs = useAppStore((s) => s.prefs);

  const enabled = !!destination && origins.length > 0;

  return useQuery({
    queryKey: [
      "compare",
      destination?.postcode,
      origins.map((o) => `${o.postcode}:${o.council_tax_band ?? ""}`),
      prefs.days_per_week,
      prefs.time_bucket,
      prefs.journey_preference,
      prefs.bedroom_category,
      prefs.council_tax_band,
    ],
    queryFn: () =>
      api.compare({
        destination: destination!.postcode,
        origins: origins.map((o) => ({
          postcode: o.postcode,
          council_tax_band: o.council_tax_band ?? null,
        })),
        prefs,
      }),
    enabled,
    staleTime: 10 * 60_000,
  });
}
