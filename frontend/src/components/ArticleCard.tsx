import { formatDistanceToNow } from "date-fns";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateArticle } from "@/api/client";
import type { Article } from "@/types";
import clsx from "clsx";

interface Props {
  article: Article;
  compact?: boolean;
}

export default function ArticleCard({ article, compact = false }: Props) {
  const qc = useQueryClient();

  const toggleRead = useMutation({
    mutationFn: () => updateArticle(article.id, { is_read: !article.is_read }),
    onSuccess: () => qc.invalidateQueries(),
  });

  const toggleBookmark = useMutation({
    mutationFn: () => updateArticle(article.id, { is_bookmarked: !article.is_bookmarked }),
    onSuccess: () => qc.invalidateQueries(),
  });

  const date = article.published_at
    ? formatDistanceToNow(new Date(article.published_at), { addSuffix: true })
    : null;

  return (
    <div
      className={clsx(
        "card group transition-all hover:border-gray-700",
        article.is_read && "opacity-50"
      )}
    >
      <div className="flex items-start gap-3">
        {/* Read indicator */}
        <button
          onClick={() => toggleRead.mutate()}
          className={clsx(
            "mt-1 h-2 w-2 flex-shrink-0 rounded-full transition-colors",
            article.is_read ? "bg-gray-600" : "bg-accent"
          )}
          title={article.is_read ? "Mark unread" : "Mark read"}
        />

        <div className="flex-1 min-w-0">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => !article.is_read && toggleRead.mutate()}
            className="text-sm font-medium text-gray-100 hover:text-white line-clamp-2 leading-snug"
          >
            {article.title}
          </a>

          {!compact && article.description && (
            <p className="mt-1 text-xs text-gray-500 line-clamp-2">{article.description}</p>
          )}

          <div className="mt-2 flex items-center gap-3 text-xs text-gray-600">
            {article.source_name && (
              <span className="text-gray-500">{article.source_name}</span>
            )}
            {date && <span>{date}</span>}
          </div>
        </div>

        {/* Bookmark */}
        <button
          onClick={() => toggleBookmark.mutate()}
          className={clsx(
            "flex-shrink-0 text-sm transition-colors",
            article.is_bookmarked ? "text-yellow-400" : "text-gray-700 hover:text-gray-400"
          )}
          title="Bookmark"
        >
          {article.is_bookmarked ? "★" : "☆"}
        </button>
      </div>
    </div>
  );
}
