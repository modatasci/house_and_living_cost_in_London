import { useState } from "react";
import { ArrowBigUp, Check, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { FUTURE_FEATURES } from "@/lib/future-features";
import { getVotedFeatures } from "@/lib/voter-id";
import { useCastVote, useVotes } from "@/hooks/use-votes";

export function FutureWorkSection() {
  const { data, isLoading, isError } = useVotes();
  const castVote = useCastVote();
  const [voted, setVoted] = useState<Set<string>>(() => getVotedFeatures());

  const handleVote = (key: string) => {
    if (voted.has(key) || castVote.isPending) return;
    setVoted((prev) => new Set(prev).add(key));
    castVote.mutate(key, {
      onError: () =>
        setVoted((prev) => {
          const next = new Set(prev);
          next.delete(key);
          return next;
        }),
    });
  };

  return (
    <section className="border-t bg-background">
      <div className="mx-auto w-full max-w-7xl px-4 py-10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold tracking-tight">Need more features?</h2>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          This is an early version. We are currently working on a number of features. Upvote the features you'd find most useful!
        </p>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {FUTURE_FEATURES.map((f) => {
            const count = data?.counts[f.key] ?? 0;
            const hasVoted = voted.has(f.key);
            return (
              <div
                key={f.key}
                className="flex flex-col justify-between gap-3 rounded-xl border bg-card p-4 shadow-sm"
              >
                <div>
                  <h3 className="text-sm font-semibold">{f.title}</h3>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {f.description}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleVote(f.key)}
                  disabled={hasVoted || castVote.isPending}
                  aria-pressed={hasVoted}
                  className={cn(
                    "flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
                    hasVoted
                      ? "border-primary/40 bg-primary/10 text-primary"
                      : "hover:bg-secondary",
                    "disabled:cursor-default"
                  )}
                >
                  <span className="flex items-center gap-1.5">
                    {hasVoted ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <ArrowBigUp className="h-4 w-4" />
                    )}
                    {hasVoted ? "Upvoted" : "Upvote"}
                  </span>
                  <span className="tabular-nums text-muted-foreground">
                    {isLoading ? "…" : isError ? "—" : count}
                  </span>
                </button>
              </div>
            );
          })}
        </div>

        {isError && (
          <p className="mt-4 text-xs text-muted-foreground">
            Vote counts are temporarily unavailable, but your vote will still be recorded.
          </p>
        )}
      </div>
    </section>
  );
}
