import type { TrendDirection } from "@/types";
import clsx from "clsx";

const MAP: Record<TrendDirection, { icon: string; color: string; label: string }> = {
  rising: { icon: "↑", color: "text-emerald-400", label: "Rising" },
  falling: { icon: "↓", color: "text-red-400", label: "Falling" },
  stable: { icon: "→", color: "text-gray-400", label: "Stable" },
  new: { icon: "✦", color: "text-yellow-400", label: "New" },
};

export default function TrendBadge({ trend }: { trend: TrendDirection | null }) {
  if (!trend) return null;
  const { icon, color, label } = MAP[trend];
  return (
    <span className={clsx("text-xs font-medium", color)} title={label}>
      {icon}
    </span>
  );
}
