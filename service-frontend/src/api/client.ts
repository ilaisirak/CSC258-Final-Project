// Unified API client. Default to mock; flip to HTTP per-namespace via env vars.
//   VITE_API_MODE=mock|http               (global default)
//   VITE_API_USERS=mock|http              (per-namespace overrides)
//   VITE_API_CLASSES=...
//   VITE_API_ASSIGNMENTS=...
//   VITE_API_SUBMISSIONS=...
//   VITE_API_GRADING=...
import type { ApiClient } from "./adapters/interfaces";
import { mockClient } from "./adapters/mock";
import { httpClient } from "./adapters/http";

type Namespace = keyof ApiClient;

const globalMode = (import.meta.env.VITE_API_MODE ?? "mock") as "mock" | "http";

const overrides: Partial<Record<Namespace, "mock" | "http">> = {
  users: import.meta.env.VITE_API_USERS,
  classes: import.meta.env.VITE_API_CLASSES,
  assignments: import.meta.env.VITE_API_ASSIGNMENTS,
  submissions: import.meta.env.VITE_API_SUBMISSIONS,
  grading: import.meta.env.VITE_API_GRADING,
};

function pick<K extends Namespace>(ns: K): ApiClient[K] {
  const mode = overrides[ns] ?? globalMode;
  return (mode === "http" ? httpClient[ns] : mockClient[ns]) as ApiClient[K];
}

export const api: ApiClient = {
  users: pick("users"),
  classes: pick("classes"),
  assignments: pick("assignments"),
  submissions: pick("submissions"),
  grading: pick("grading"),
};

console.log("API MODE:", import.meta.env.VITE_API_MODE);