import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "@/components/Layout";
import ErrorBoundary from "@/components/ErrorBoundary";

// Lazy-load pages so a crash in one doesn't take down the whole app
const DigestPage = lazy(() => import("@/pages/Digest"));
const Feed = lazy(() => import("@/pages/Feed"));
const GraphPage = lazy(() => import("@/pages/Graph"));
const Sources = lazy(() => import("@/pages/Sources"));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full">
      <span className="text-gray-500 text-sm">Loading…</span>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route
          index
          element={
            <ErrorBoundary>
              <Suspense fallback={<PageLoader />}>
                <DigestPage />
              </Suspense>
            </ErrorBoundary>
          }
        />
        <Route
          path="feed"
          element={
            <ErrorBoundary>
              <Suspense fallback={<PageLoader />}>
                <Feed />
              </Suspense>
            </ErrorBoundary>
          }
        />
        <Route
          path="graph"
          element={
            <ErrorBoundary>
              <Suspense fallback={<PageLoader />}>
                <GraphPage />
              </Suspense>
            </ErrorBoundary>
          }
        />
        <Route
          path="sources"
          element={
            <ErrorBoundary>
              <Suspense fallback={<PageLoader />}>
                <Sources />
              </Suspense>
            </ErrorBoundary>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
