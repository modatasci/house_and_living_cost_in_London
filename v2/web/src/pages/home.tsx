import { useEffect, useRef } from "react";
import { ChevronDown } from "lucide-react";
import { LondonMap } from "@/components/map/london-map";
import { FloatingControls } from "@/components/floating-controls";
import { HeroHeader } from "@/components/hero-header";
import { ResultsSection } from "@/components/results-section";
import { FutureWorkSection } from "@/components/future-work-section";
import { useAppStore } from "@/store/app-store";

export function HomePage() {
  const hydrateFromUrl = useAppStore((s) => s.hydrateFromUrl);
  const resultsRef = useRef<HTMLElement>(null);

  useEffect(() => {
    hydrateFromUrl();
  }, [hydrateFromUrl]);

  return (
    <div>
      {/* Hero: title + steps, then a contained, framed map */}
      <section className="pb-10">
        <HeroHeader />

        <div className="mx-auto w-full max-w-7xl px-4">
          <div className="relative h-[68vh] min-h-[460px] overflow-hidden rounded-2xl border shadow-sm">
            <LondonMap />
            <FloatingControls />

            <button
              type="button"
              onClick={() =>
                resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
              }
              className="group absolute inset-x-0 bottom-4 z-10 mx-auto flex w-fit items-center gap-1.5 rounded-full border bg-background/80 px-3 py-1.5 text-xs font-medium shadow-md backdrop-blur transition-colors hover:bg-background"
            >
              See results
              <ChevronDown className="h-3.5 w-3.5 animate-bounce group-hover:animate-none" />
            </button>
          </div>
        </div>
      </section>

      <ResultsSection ref={resultsRef} />

      <FutureWorkSection />
    </div>
  );
}
