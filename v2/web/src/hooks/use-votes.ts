import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { castVote, fetchVoteCounts, type VoteCounts } from "@/lib/votes-api";
import { getVoterId, markVoted } from "@/lib/voter-id";

export function useVotes() {
  return useQuery({
    queryKey: ["votes"],
    queryFn: fetchVoteCounts,
    staleTime: 60_000,
  });
}

export function useCastVote() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (featureKey: string) => castVote(getVoterId(), featureKey),
    onMutate: async (featureKey: string) => {
      await qc.cancelQueries({ queryKey: ["votes"] });
      const prev = qc.getQueryData<VoteCounts>(["votes"]);
      qc.setQueryData<VoteCounts>(["votes"], (old) =>
        old
          ? {
              counts: {
                ...old.counts,
                [featureKey]: (old.counts[featureKey] ?? 0) + 1,
              },
            }
          : old
      );
      return { prev };
    },
    onError: (_err, _key, ctx) => {
      if (ctx?.prev) qc.setQueryData(["votes"], ctx.prev);
    },
    onSuccess: (_data, featureKey) => {
      markVoted(featureKey);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["votes"] });
    },
  });
}
