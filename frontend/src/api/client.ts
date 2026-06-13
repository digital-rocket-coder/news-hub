import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : import.meta.env.DEV
  ? "/api"
  : "https://news-hub-production-7188.up.railway.app/api";

const api = axios.create({ baseURL });

// Reject if the server returns HTML instead of JSON (e.g. Vercel fallback page)
api.interceptors.response.use(
  (res) => {
    const ct = res.headers["content-type"] ?? "";
    if (ct.includes("text/html")) {
      return Promise.reject(new Error("Expected JSON but received HTML"));
    }
    return res;
  },
  (err) => Promise.reject(err)
);

export default api;

// ── Sources ──────────────────────────────────────────────────────────────────

export const getSources = () => api.get("/sources/").then((r) => r.data);
export const createSource = (body: { url: string; name: string; category?: string; poll_interval?: number }) =>
  api.post("/sources/", body).then((r) => r.data);
export const updateSource = (id: number, body: object) =>
  api.patch(`/sources/${id}`, body).then((r) => r.data);
export const deleteSource = (id: number) => api.delete(`/sources/${id}`);
export const pollSource = (id: number) => api.post(`/sources/${id}/poll`);

// ── Articles ─────────────────────────────────────────────────────────────────

export const getArticles = (params?: object) =>
  api.get("/articles/", { params }).then((r) => r.data);
export const updateArticle = (id: number, body: object) =>
  api.patch(`/articles/${id}`, body).then((r) => r.data);
export const markAllRead = (topic_id?: number) =>
  api.post("/articles/mark-all-read", null, { params: topic_id ? { topic_id } : {} });

// ── Topics ───────────────────────────────────────────────────────────────────

export const getTopics = (include_muted = false) =>
  api.get("/topics/", { params: { include_muted } }).then((r) => r.data);
export const getTopic = (id: number) =>
  api.get(`/topics/${id}`).then((r) => r.data);
export const createTopic = (body: { name: string; keywords?: string }) =>
  api.post("/topics/", body).then((r) => r.data);
export const updateTopic = (id: number, body: object) =>
  api.patch(`/topics/${id}`, body).then((r) => r.data);
export const deleteTopic = (id: number) => api.delete(`/topics/${id}`);
export const getTopicTrends = (id: number) =>
  api.get(`/topics/${id}/trends`).then((r) => r.data);
export const getClusters = () =>
  api.get("/topics/clusters/pending").then((r) => r.data);
export const confirmCluster = (body: { cluster_id: number; name: string; accept: boolean }) =>
  api.post("/topics/clusters/confirm", body);
export const triggerRecluster = () => api.post("/topics/recluster");

// ── Digest ───────────────────────────────────────────────────────────────────

export const getDigest = (since_days = 7) =>
  api.get("/digest/", { params: { since_days } }).then((r) => r.data);

// ── Graph ────────────────────────────────────────────────────────────────────

export const getGraph = () => api.get("/graph/").then((r) => r.data);
