import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import {
  getSources,
  createSource,
  updateSource,
  deleteSource,
  pollSource,
} from "@/api/client";
import type { Source } from "@/types";

function SourceRow({ source }: { source: Source }) {
  const qc = useQueryClient();

  const toggle = useMutation({
    mutationFn: () => updateSource(source.id, { is_active: !source.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  const remove = useMutation({
    mutationFn: () => deleteSource(source.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  const poll = useMutation({
    mutationFn: () => pollSource(source.id),
  });

  return (
    <div className="card flex items-center gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-white">{source.name}</span>
          {source.category && (
            <span className="badge bg-gray-800 text-gray-400">{source.category}</span>
          )}
          {!source.is_active && (
            <span className="badge bg-gray-800 text-gray-500">paused</span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-0.5 truncate">{source.url}</p>
        {source.last_polled_at && (
          <p className="text-xs text-gray-600 mt-0.5">
            polled {formatDistanceToNow(new Date(source.last_polled_at), { addSuffix: true })}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={() => poll.mutate()}
          disabled={poll.isPending}
          className="btn-ghost text-xs"
          title="Poll now"
        >
          {poll.isPending ? "↻ polling…" : "↻ poll"}
        </button>
        <button
          onClick={() => toggle.mutate()}
          className="btn-ghost text-xs"
        >
          {source.is_active ? "pause" : "resume"}
        </button>
        <button
          onClick={() => {
            if (confirm(`Delete "${source.name}"?`)) remove.mutate();
          }}
          className="btn-ghost text-xs text-red-400 hover:text-red-300"
        >
          delete
        </button>
      </div>
    </div>
  );
}

function AddSourceForm({ onDone }: { onDone: () => void }) {
  const qc = useQueryClient();
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [error, setError] = useState("");

  const add = useMutation({
    mutationFn: () =>
      createSource({ url, name, category: category || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sources"] });
      onDone();
    },
    onError: (e: any) => setError(e.response?.data?.detail || "Failed to add source"),
  });

  return (
    <div className="card space-y-3">
      <h3 className="text-sm font-semibold text-white">Add RSS Source</h3>
      <div className="grid grid-cols-2 gap-3">
        <input
          className="input col-span-2"
          placeholder="RSS feed URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <input
          className="input"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="input"
          placeholder="Category (optional)"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <div className="flex gap-2">
        <button
          className="btn-primary"
          disabled={!url || !name || add.isPending}
          onClick={() => add.mutate()}
        >
          {add.isPending ? "Adding…" : "Add source"}
        </button>
        <button className="btn-ghost" onClick={onDone}>
          Cancel
        </button>
      </div>
    </div>
  );
}

export default function Sources() {
  const [showForm, setShowForm] = useState(false);
  const { data: sources = [], isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: getSources,
  });

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Sources</h1>
          <p className="text-sm text-gray-500 mt-0.5">RSS feeds you're tracking</p>
        </div>
        {!showForm && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + Add source
          </button>
        )}
      </div>

      {showForm && <AddSourceForm onDone={() => setShowForm(false)} />}

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : sources.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 text-sm">No sources yet.</p>
          <p className="text-gray-600 text-xs mt-1">Add an RSS feed to get started.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map((s: Source) => (
            <SourceRow key={s.id} source={s} />
          ))}
        </div>
      )}
    </div>
  );
}
