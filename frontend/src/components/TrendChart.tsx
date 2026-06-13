import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import type { TrendPoint } from "@/types";

export default function TrendChart({ points }: { points: TrendPoint[] }) {
  const data = points.map((p) => ({
    week: format(new Date(p.period_start), "MMM d"),
    count: p.weight,
  }));

  return (
    <ResponsiveContainer width="100%" height={80}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: -28, bottom: 0 }}>
        <defs>
          <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#e94560" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#e94560" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="week" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} allowDecimals={false} />
        <Tooltip
          contentStyle={{ background: "#1a1a2e", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#9ca3af" }}
          itemStyle={{ color: "#e94560" }}
        />
        <Area type="monotone" dataKey="count" stroke="#e94560" fill="url(#grad)" strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
