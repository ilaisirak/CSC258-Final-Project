// Unified API client. All namespaces are backed by the HTTP adapter,
// which routes through the gateway at VITE_API_BASE (default /api).
import type { ApiClient } from "./adapters/interfaces";
import { httpClient } from "./adapters/http";

export const api: ApiClient = httpClient;
