const STEPS = [
  "Select work address",
  "Select rent address",
  "Evaluate cost and time-to-commute",
];

export function HeroHeader() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-6 pt-8 text-center">
      <h1 className="text-3xl font-extrabold uppercase tracking-tight sm:text-4xl">
        Find the best rent in <span className="text-primary">London</span>
      </h1>
      <div className="mt-5 flex flex-col items-center justify-center gap-x-10 gap-y-3 sm:flex-row">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-400 text-sm font-bold text-amber-950 shadow-sm">
              {i + 1}
            </span>
            <span className="text-sm font-semibold uppercase tracking-wide text-foreground/80">
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
