import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDigest } from "@/api/client";
import type { Digest, DigestTopicItem } from "@/types";
import ArticleCard from "@/components/ArticleCard";
import TrendBadge from "@/components/TrendBadge";
import clsx from "clsx";

const PERIOD_OPTIONS = [
  { label: "Today", days: 1 },
  { label: "Week", days: 7 },
  { label: "Month", days: 30 },
  { label: "3 months", days: 90 },
];

function DigestItem({ item }: { item: DigestTopicItem }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-white">{item.topic.name}</h3>
            <TrendBadge trend={item.topic.trend} />
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {item.topic.unread_count} unread · {item.topic.article_count} total
          </p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="btn-ghost text-xs"
        >
          {expanded ? "Collapse" : "Expand"}
        </button>
      </div>

      {item.summary && (
        <p className="text-sm text-gray-300 leading-relaxed border-l-2 border-accent/40 pl-3">
          {item.summary}
        </p>
      )}

      <div className={clsx("space-y-2", !expanded && "max-h-0 overflow-hidden")}>
        {expanded && item.key_articles.map((a) => (
          <ArticleCard key={a.id} article={a} compact />
        ))}
      </div>

      {!expanded && item.key_articles.length > 0 && (
        <div className="space-y-1">
          {item.key_articles.map((a) => (
            <a
              key={a.id}
              href={a.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-xs text-gray-400 hover:text-white truncate"
            >
              · {a.title}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DigestPage() {
  const [days, setDays] = useState(7);

  const { data: digest, isLoading, refetch } = useQuery<Digest>({
    queryKey: ["digest", days],
    queryFn: () => getDigest(days),
  });

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Digest</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {digest ? `${digest.period_label} · ${digest.items.length} top topics` : "What matters right now"}
          </p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost text-xs">
          ↻ refresh
        </button>
      </div>

      {/* Period selector */}
      <div className="flex gap-2">
        {PERIOD_OPTIONS.map((opt) => (
          <button
            key={opt.days}
            onClick={() => setDays(opt.days)}
            className={clsx(
              "btn text-xs",
              days === opt.days
                ? "bg-accent/15 text-accent border border-accent/30"
                : "btn-ghost"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="text-sm text-gray-500">Generating digest…</div>
      ) : !digest || digest.items.length === 0 ? (
        <div className="card text-center py-16">
          <p className="text-5xl mb-4">✦</p>
          <p className="text-gray-400 text-sm">Nothing to digest yet.</p>
          <p className="text-gray-600 text-xs mt-1">
            Add RSS sources so articles start accumulating.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {digest.items.map((item, i) => (
            <DigestItem key={item.topic.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
