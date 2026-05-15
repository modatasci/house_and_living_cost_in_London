import {
  CartesianGrid,
  Label,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { TrendingUp } from "lucide-react";
import { useCompare } from "@/hooks/use-compare";
import { useAppStore } from "@/store/app-store";
import { paretoFrontier } from "@/lib/pareto";
import { formatGBP, formatMinutes } from "@/lib/utils";
import type { OriginResult } from "@/types/api";

const HOME_COLORS = ["#2563eb", "#9333ea", "#db2777", "#ea580c", "#ca8a04"];

interface ChartPoint {
  index: number;
  postcode: string;
  borough: string | null;
  time: number;
  cost: number;
  color: string;
  pareto: boolean;
  result: OriginResult;
}

export function CostChart() {
  const { data, isFetching, error } = useCompare();
  const destination = useAppStore((s) => s.destination);
  const origins = useAppStore((s) => s.origins);

  if (!destination) {
    return <Empty icon="setup">Set an office to start comparing.</Empty>;
  }
  if (!origins.length) {
    return <Empty icon="setup">Add at least one home to see the cost vs commute chart.</Empty>;
  }
  if (isFetching && !data) {
    return <Empty icon="loading">Fetching journeys from TfL…</Empty>;
  }
  if (error) {
    return <Empty icon="error">Couldn't reach the API.</Empty>;
  }
  if (!data) return null;

  // Build chart points only for results that have both a time and a cost.
  const successful = data.results
    .map((r, i) => ({ r, i }))
    .filter(({ r }) => r.journey.duration_minutes != null);

  if (successful.length === 0) {
    const errs = data.results.filter((r) => r.error).map((r) => r.error);
    return (
      <Empty icon="error">
        No journey results. {errs[0] ?? "Check that the API has a TfL key configured."}
      </Empty>
    );
  }

  const candidates: ChartPoint[] = successful.map(({ r, i }) => ({
    index: i,
    postcode: r.origin,
    borough: r.borough_name,
    time: r.journey.duration_minutes ?? 0,
    cost: r.cost.monthly_total_gbp,
    color: HOME_COLORS[i % HOME_COLORS.length],
    pareto: false,
    result: r,
  }));
  const winners = paretoFrontier(candidates);
  candidates.forEach((p) => (p.pareto = winners.has(p)));

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 24, bottom: 28, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              type="number"
              dataKey="time"
              name="Commute"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v) => `${v}m`}
              domain={["dataMin - 5", "dataMax + 5"]}
            >
              <Label
                value="Door-to-door minutes"
                position="bottom"
                offset={10}
                style={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              />
            </XAxis>
            <YAxis
              type="number"
              dataKey="cost"
              name="Monthly cost"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v) => formatGBP(v)}
              domain={["dataMin - 100", "dataMax + 100"]}
              width={70}
            />
            <ZAxis range={[140, 140]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={<PointTooltip />}
              wrapperStyle={{ outline: "none" }}
            />
            <Scatter data={candidates} shape={<PointShape />} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function PointShape(props: {
  cx?: number;
  cy?: number;
  payload?: ChartPoint;
}) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null || !payload) return null;
  const r = payload.pareto ? 9 : 7;
  return (
    <g>
      {payload.pareto && (
        <circle cx={cx} cy={cy} r={r + 4} fill={payload.color} opacity={0.18} />
      )}
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill={payload.color}
        stroke="white"
        strokeWidth={payload.pareto ? 2.5 : 1.5}
      />
      <text
        x={cx}
        y={cy}
        dy={3.5}
        textAnchor="middle"
        fontSize={10}
        fontWeight={700}
        fill="white"
        style={{ pointerEvents: "none" }}
      >
        {payload.index + 1}
      </text>
    </g>
  );
}

function PointTooltip({ active, payload }: { active?: boolean; payload?: { payload: ChartPoint }[] }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  const r = p.result;
  return (
    <div className="rounded-md border bg-card px-3 py-2 text-xs shadow-md">
      <div className="mb-1 flex items-center gap-1.5 font-semibold">
        <span
          className="inline-flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold text-white"
          style={{ background: p.color }}
        >
          {p.index + 1}
        </span>
        {p.postcode}
        {p.pareto && (
          <span className="ml-1 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
            Best value
          </span>
        )}
      </div>
      {p.borough && <div className="text-muted-foreground">{p.borough}</div>}
      <div className="mt-1.5 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
        <span className="text-muted-foreground">Journey</span>
        <span className="text-right tabular-nums">{formatMinutes(p.time)}</span>
        <span className="text-muted-foreground">Commute</span>
        <span className="text-right tabular-nums">
          {formatGBP(r.cost.monthly_commute_gbp)}/mo
        </span>
        <span className="text-muted-foreground">Rent</span>
        <span className="text-right tabular-nums">
          {formatGBP(r.cost.monthly_rent_gbp)}/mo
        </span>
        <span className="text-muted-foreground">Council tax</span>
        <span className="text-right tabular-nums">
          {formatGBP(r.cost.monthly_council_tax_gbp)}/mo
        </span>
        <span className="font-semibold">Total</span>
        <span className="text-right font-semibold tabular-nums">
          {formatGBP(r.cost.monthly_total_gbp)}/mo
        </span>
      </div>
    </div>
  );
}

function Empty({ icon, children }: { icon: "setup" | "loading" | "error"; children: React.ReactNode }) {
  return (
    <div className="flex h-full items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-2 px-6 text-center text-muted-foreground">
        <TrendingUp className={icon === "loading" ? "h-8 w-8 animate-pulse opacity-50" : "h-8 w-8 opacity-50"} />
        <p className="max-w-sm text-sm">{children}</p>
      </div>
    </div>
  );
}
