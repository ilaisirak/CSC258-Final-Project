/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_MODE?: "mock" | "http";
  readonly VITE_API_BASE?: string;
  readonly VITE_API_USERS?: "mock" | "http";
  readonly VITE_API_CLASSES?: "mock" | "http";
  readonly VITE_API_ASSIGNMENTS?: "mock" | "http";
  readonly VITE_API_SUBMISSIONS?: "mock" | "http";
  readonly VITE_API_GRADING?: "mock" | "http";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
