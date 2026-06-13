import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getTopics,
  getTopic,
  updateTopic,
  markAllRead,
  getTopicTrends,
  getClusters,
  confirmCluster,
  triggerRecluster,
} from "@/api/client";
import type { Topic, TopicWithArticles, ClusterCandidate } from "@/types";
import ArticleCard from "@/components/ArticleCard";
import TrendBadge from "@/components/TrendBadge";
import TrendChart from "@/components/TrendChart";
import clsx from "clsx";

function ClusterReview() {
  const qc = useQueryClient();
  const { data: clusters = [] } = useQuery<ClusterCandidate[]>({
    queryKey: ["clusters"],
    queryFn: getClusters,
  });

  const confirm = useMutation({
    mutationFn: confirmCluster,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clusters"] });
      qc.invalidateQueries({ queryKey: ["topics"] });
    },
  });

  const [names, setNames] = useState<Record<number, string>>({});

  if (!clusters.length) return null;

  return (
    <div className="card border-yellow-700/50 bg-yellow-950/20 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-yellow-400">
          {clusters.length} new topic cluster{clusters.length > 1 ? "s" : ""} to review
        </h3>
      </div>
      <div className="space-y-3">
        {clusters.map((c: ClusterCandidate) => (
          <div key={c.cluster_id} className="flex items-start gap-3">
            <div className="flex-1">
              <input
                className="input text-xs"
                value={names[c.cluster_id] ?? c.suggested_name}
                onChange={(e) =>
                  setNames((prev) => ({ ...prev, [c.cluster_id]: e.target.value }))
                }
              />
              <p className="text-xs text-gray-500 mt-1">
                {c.article_count} articles · {c.sample_titles.slice(0, 2).join(" · ")}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                className="btn-primary text-xs"
                onClick={() =>
                  confirm.mutate({
                    cluster_id: c.cluster_id,
                    name: names[c.cluster_id] ?? c.suggested_name,
                    accept: true,
                  })
                }
              >
                Keep
              </button>
              <button
                className="btn-ghost text-xs text-red-400"
                onClick={() =>
                  confirm.mutate({
                    cluster_id: c.cluster_id,
                    name: c.suggested_name,
                    accept: false,
                  })
                }
              >
                Drop
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TopicPanel({ topic, onClose }: { topic: Topic; onClose: () => void }) {
  const qc = useQueryClient();

  const { data: detail } = useQuery<TopicWithArticles>({
    queryKey: ["topic", topic.id],
    queryFn: () => getTopic(topic.id),
  });

  const { data: trends } = useQuery({
    queryKey: ["topic-trends", topic.id],
    queryFn: () => getTopicTrends(topic.id),
  });

  const mute = useMutation({
    mutationFn: () => updateTopic(topic.id, { is_muted: !topic.is_muted }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["topics"] });
      onClose();
    },
  });

  const readAll = useMutation({
    mutationFn: () => markAllRead(topic.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["topic", topic.id] });
      qc.invalidateQueries({ queryKey: ["topics"] });
    },
  });

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-white">{topic.name}</h2>
            <TrendBadge trend={topic.trend} />
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {topic.unread_count} unread · {topic.article_count} total
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost text-xs" onClick={() => readAll.mutate()}>
            Mark all read
          </button>
          <button className="btn-ghost text-xs" onClick={() => mute.mutate()}>
            {topic.is_muted ? "Unmute" : "Mute"}
          </button>
          <button className="btn-ghost" onClick={onClose}>
            ✕
          </button>
        </div>
      </div>

      {trends?.points?.length > 0 && (
        <div className="px-4 pt-3">
          <TrendChart points={trends.points} />
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {detail?.articles?.map((a) => (
          <ArticleCard key={a.id} article={a} />
        ))}
      </div>
    </div>
  );
}

function TopicCard({
  topic,
  isSelected,
  onClick,
}: {
  topic: Topic;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full text-left card transition-all hover:border-gray-600",
        isSelected && "border-accent/50 bg-accent/5"
      )}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium text-sm text-white line-clamp-1">{topic.name}</span>
        <TrendBadge trend={topic.trend} />
      </div>
      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
        {topic.unread_count > 0 && (
          <span className="text-accent font-semibold">{topic.unread_count} new</span>
        )}
        <span>{topic.article_count} articles</span>
        {topic.type === "manual" && (
          <span className="badge bg-gray-800 text-gray-500">manual</span>
        )}
      </div>
    </button>
  );
}

export default function Feed() {
  const qc = useQueryClient();
  const [searchParams] = useSearchParams();
  const [selectedId, setSelectedId] = useState<number | null>(
    searchParams.get("topic") ? Number(searchParams.get("topic")) : null
  );
  const [showMuted, setShowMuted] = useState(false);

  useEffect(() => {
    const id = searchParams.get("topic");
    if (id) setSelectedId(Number(id));
  }, [searchParams]);

  const { data: topics = [], isLoading } = useQuery<Topic[]>({
    queryKey: ["topics", showMuted],
    queryFn: () => getTopics(showMuted),
    refetchInterval: 60_000,
  });

  const recluster = useMutation({
    mutationFn: triggerRecluster,
    onSuccess: () => {
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ["topics"] });
        qc.invalidateQueries({ queryKey: ["clusters"] });
      }, 2000);
    },
  });

  const selectedTopic = topics.find((t) => t.id === selectedId) ?? null;

  return (
    <div className="flex h-full">
      {/* Topic list */}
      <div className="w-72 flex-shrink-0 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center justify-between mb-1">
            <h1 className="text-lg font-bold text-white">Topics</h1>
            <button
              onClick={() => recluster.mutate()}
              disabled={recluster.isPending}
              className="btn-ghost text-xs"
              title="Re-run clustering"
            >
              {recluster.isPending ? "↻…" : "↻"}
            </button>
          </div>
          <button
            className="text-xs text-gray-500 hover:text-gray-300"
            onClick={() => setShowMuted(!showMuted)}
          >
            {showMuted ? "Hide muted" : "Show muted"}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          <ClusterReview />
          {isLoading ? (
            <p className="text-sm text-gray-500 px-1">Loading…</p>
          ) : topics.length === 0 ? (
            <p className="text-sm text-gray-500 px-1">
              No topics yet. Add sources and articles will cluster automatically.
            </p>
          ) : (
            topics.map((t) => (
              <TopicCard
                key={t.id}
                topic={t}
                isSelected={t.id === selectedId}
                onClick={() => setSelectedId(t.id === selectedId ? null : t.id)}
              />
            ))
          )}
        </div>
      </div>

      {/* Article panel */}
      <div className="flex-1 overflow-hidden">
        {selectedTopic ? (
          <TopicPanel topic={selectedTopic} onClose={() => setSelectedId(null)} />
        ) : (
          <div className="flex items-center justify-center h-full text-center px-8">
            <div>
              <p className="text-4xl mb-4">⊞</p>
              <p className="text-gray-400 text-sm">Select a topic to read its articles</p>
              <p className="text-gray-600 text-xs mt-1">
                Articles are clustered by semantic similarity
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
