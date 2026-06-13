import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "@/components/Layout";
import DigestPage from "@/pages/Digest";
import Feed from "@/pages/Feed";
import GraphPage from "@/pages/Graph";
import Sources from "@/pages/Sources";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DigestPage />} />
        <Route path="feed" element={<Feed />} />
        <Route path="graph" element={<GraphPage />} />
        <Route path="sources" element={<Sources />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
