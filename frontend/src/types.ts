export type SourceType = "rss";
export type TopicType = "auto" | "manual";
export type TrendDirection = "rising" | "falling" | "stable" | "new";

export interface Source {
  id: number;
  type: SourceType;
  url: string;
  name: string;
  category: string | null;
  poll_interval: number;
  last_polled_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Article {
  id: number;
  source_id: number;
  title: string;
  url: string;
  published_at: string | null;
  fetched_at: string;
  description: string | null;
  summary: string | null;
  is_read: boolean;
  is_bookmarked: boolean;
  source_name: string | null;
}

export interface Topic {
  id: number;
  name: string;
  type: TopicType;
  keywords: string | null;
  is_muted: boolean;
  trend: TrendDirection | null;
  created_at: string;
  article_count: number;
  unread_count: number;
}

export interface TopicWithArticles extends Topic {
  articles: Article[];
}

export interface TrendPoint {
  period_start: string;
  weight: number;
}

export interface TopicTrend {
  topic_id: number;
  topic_name: string;
  direction: TrendDirection | null;
  points: TrendPoint[];
}

export interface GraphNode {
  id: number;
  name: string;
  article_count: number;
  trend: TrendDirection | null;
  is_muted: boolean;
  // added by react-force-graph at runtime
  x?: number;
  y?: number;
}

export interface GraphEdge {
  source: number;
  target: number;
  strength: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DigestTopicItem {
  topic: Topic;
  key_articles: Article[];
  summary: string | null;
}

export interface Digest {
  period_label: string;
  days_away: number;
  items: DigestTopicItem[];
}

export interface ClusterCandidate {
  cluster_id: number;
  suggested_name: string;
  article_count: number;
  sample_titles: string[];
}
