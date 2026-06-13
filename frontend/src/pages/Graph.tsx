import { useRef, useCallback, useState, useEffect, lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getGraph } from "@/api/client";
import type { GraphData, GraphNode, GraphEdge } from "@/types";
import TrendBadge from "@/components/TrendBadge";

// Dynamic import to isolate canvas/D3 initialisation from the module graph
const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

const TREND_COLORS: Record<string, string> = {
  rising: "#34d399",
  new: "#fbbf24",
  falling: "#f87171",
  stable: "#9ca3af",
};

function nodeColor(node: GraphNode): string {
  if (node.trend && TREND_COLORS[node.trend]) return TREND_COLORS[node.trend];
  return "#6366f1";
}

function nodeSize(node: GraphNode): number {
  return Math.max(4, Math.min(20, 4 + node.article_count * 0.8));
}

export default function GraphPage() {
  const navigate = useNavigate();
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const [hovered, setHovered] = useState<GraphNode | null>(null);

  const { data: graphData, isLoading } = useQuery<GraphData>({
    queryKey: ["graph"],
    queryFn: getGraph,
    refetchInterval: 60_000,
  });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      setDims({ w: el.clientWidth, h: el.clientHeight });
    });
    obs.observe(el);
    setDims({ w: el.clientWidth, h: el.clientHeight });
    return () => obs.disconnect();
  }, []);

  const safeNodes = Array.isArray(graphData?.nodes) ? graphData.nodes : [];
  const safeEdges = Array.isArray(graphData?.edges) ? graphData.edges : [];
  const fgData = {
    nodes: safeNodes.map((n) => ({ ...n })),
    links: safeEdges.map((e: GraphEdge) => ({
      source: e.source,
      target: e.target,
      strength: e.strength,
    })),
  };

  const handleNodeClick = useCallback(
    (node: any) => navigate(`/feed?topic=${node.id}`),
    [navigate]
  );

  const handleNodeHover = useCallback((node: any | null) => {
    setHovered(node as GraphNode | null);
  }, []);

  const drawNode = useCallback((node: any, ctx: CanvasRenderingContext2D) => {
    const r = nodeSize(node as GraphNode);
    const color = nodeColor(node as GraphNode);

    ctx.shadowColor = color;
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = color + "cc";
    ctx.fill();
    ctx.shadowBlur = 0;

    const fontSize = Math.max(8, Math.min(12, r + 2));
    ctx.font = `${fontSize}px Inter, sans-serif`;
    ctx.fillStyle = "#e5e7eb";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const label =
      (node as GraphNode).name.length > 18
        ? (node as GraphNode).name.slice(0, 16) + "…"
        : (node as GraphNode).name;
    ctx.fillText(label, node.x, node.y + r + fontSize);
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">Topic Graph</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Nodes = topics · Size = article count · Color = trend · Click to explore
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          {[
            { color: "#34d399", label: "Rising" },
            { color: "#fbbf24", label: "New" },
            { color: "#f87171", label: "Falling" },
            { color: "#9ca3af", label: "Stable" },
          ].map(({ color, label }) => (
            <span key={label} className="flex items-center gap-1">
              <span
                className="w-2 h-2 rounded-full inline-block"
                style={{ background: color }}
              />
              {label}
            </span>
          ))}
        </div>
      </div>

      <div ref={containerRef} className="flex-1 relative overflow-hidden bg-[#0a0a18]">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">
            Loading graph…
          </div>
        ) : fgData.nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center px-8">
            <div>
              <p className="text-5xl mb-4">◎</p>
              <p className="text-gray-400 text-sm">
                Graph will appear once topics are clustered
              </p>
            </div>
          </div>
        ) : (
          <Suspense
            fallback={
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                Loading graph engine…
              </div>
            }
          >
            <ForceGraph2D
              ref={graphRef}
              width={dims.w}
              height={dims.h}
              graphData={fgData}
              nodeId="id"
              linkSource="source"
              linkTarget="target"
              nodeCanvasObject={drawNode}
              nodeCanvasObjectMode={() => "replace"}
              onNodeClick={handleNodeClick}
              onNodeHover={handleNodeHover}
              linkColor={() => "#374151aa"}
              linkWidth={(link: any) => (link.strength ?? 0.3) * 3}
              backgroundColor="#0a0a18"
              cooldownTicks={100}
              nodeLabel=""
            />
          </Suspense>
        )}

        {hovered && (
          <div className="absolute top-4 left-4 card pointer-events-none z-10 min-w-[160px]">
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm text-white">{hovered.name}</span>
              <TrendBadge trend={hovered.trend} />
            </div>
            <p className="text-xs text-gray-500 mt-1">{hovered.article_count} articles</p>
            <p className="text-xs text-gray-600 mt-0.5">Click to open topic</p>
          </div>
        )}
      </div>
    </div>
  );
}
