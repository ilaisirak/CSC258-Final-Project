// http.ts
// HTTP adapter — maps the ApiClient interface to real backend endpoints.
// Each namespace can be enabled independently via env vars (see client.ts).
//
// Conventions:
//   POST   /api/auth/login            (form-urlencoded: username,password)
//   POST   /api/auth/refresh          (HttpOnly cookie)
//   POST   /api/auth/logout           (HttpOnly cookie)
//   POST   /api/auth/register         (JSON: email,password,name,role)
//   GET    /api/users/me              (Bearer token)
//   GET    /api/users/search?email=...
//   GET    /api/classes?studentId=... | ?professorId=...
//   GET    /api/classes/:id
//   POST   /api/classes
//   GET    /api/classes/:id/roster
//   POST   /api/classes/:id/roster/:studentId
//   POST   /api/classes/:id/roster/by-email   { email }
//   DELETE /api/classes/:id/roster/:userId
//   GET    /api/assignments?classId=...
//   GET    /api/assignments/for-student/:studentId
//   GET    /api/assignments/:id
//   POST   /api/assignments
//   GET    /api/submissions?assignmentId=... | ?studentId=...
//   POST   /api/grading
//   GET    /api/grading?studentId=...
//   GET    /api/students/:id/stats
//   GET    /api/professors/:id/stats
//   GET    /api/professors/:id/grading-queue

import type {
  AssignmentForStudent,
  GradingQueueItem,
  ProfessorStats,
  StudentStats,
  Submission,
  User,
} from "../types";
import type { ApiClient, AuthSession } from "./interfaces";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

// ---------- Token storage ----------
//
// The access token is the short-lived (15 min) JWT issued by
// service-user. It lives only in this module's memory — never in
// localStorage — so a successful XSS cannot read it. Long-lived
// session continuity is handled by the refresh-token cookie, which
// the browser sets/clears automatically on /api/auth/* responses
// and is HttpOnly so JS cannot read or exfiltrate it either.

let tokenCache: string | null = null;

export function getAuthToken(): string | null {
  return tokenCache;
}

export function setAuthToken(token: string | null) {
  tokenCache = token;
}

// ---------- Snake ⇄ camelCase conversion utilities ----------

function snakeToCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function keysToCamelCase(input: unknown): unknown {
  if (Array.isArray(input)) {
    return input.map(keysToCamelCase);
  }
  if (input !== null && typeof input === "object") {
    return Object.keys(input as Record<string, unknown>).reduce(
      (acc, key) => {
        const camelKey = snakeToCamelCase(key);
        acc[camelKey] = keysToCamelCase((input as Record<string, unknown>)[key]);
        return acc;
      },
      {} as Record<string, unknown>,
    );
  }
  return input;
}

// ---------- Refresh-token coordination ----------
//
// On a 401 we attempt one silent refresh against /api/auth/refresh.
// The refresh cookie is HttpOnly + Secure + scoped to /api/auth, so
// the browser sends it automatically and we never see the value here.
// A single in-flight promise is shared by all callers so a burst of
// 401s only triggers one refresh round-trip.

let refreshInFlight: Promise<string | null> | null = null;

async function tryRefresh(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${BASE}/auth/refresh`, {
        method: "POST",
        credentials: "same-origin",
      });
      if (!res.ok) return null;
      const data = (await res.json()) as { access_token: string };
      setAuthToken(data.access_token);
      return data.access_token;
    } catch {
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

// ---------- Generic HTTP fetch wrapper ----------
//
// Attaches the access token automatically. On 401 we attempt one
// refresh, and if that succeeds we replay the original request once.
// If refresh fails the token cache is cleared so subsequent requests
// surface as unauthenticated and AuthContext can show the login page.

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const buildHeaders = (token: string | null) => {
    const h: Record<string, string> = {
      "Content-Type": "application/json",
      ...((init?.headers as Record<string, string> | undefined) ?? {}),
    };
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
  };

  const fetchOnce = (token: string | null) =>
    fetch(`${BASE}${path}`, {
      ...init,
      headers: buildHeaders(token),
      credentials: "same-origin",
    });

  let res = await fetchOnce(tokenCache);
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetchOnce(refreshed);
    } else {
      setAuthToken(null);
    }
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(formatHttpError(res.status, res.statusText, body));
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json();
  return keysToCamelCase(data) as T;
}

// Translate a backend error response into a human-friendly message.
// FastAPI errors typically come back as { "detail": "..." } or
// { "detail": [{ "msg": "..." }] }. fastapi-users adds a small set of
// well-known error codes (REGISTER_USER_ALREADY_EXISTS, etc.) that we
// map to readable copy.
const FRIENDLY_ERRORS: Record<string, string> = {
  REGISTER_USER_ALREADY_EXISTS: "An account with that email already exists.",
  LOGIN_BAD_CREDENTIALS: "Incorrect email or password.",
  LOGIN_USER_NOT_VERIFIED: "Account is not verified.",
  REGISTER_INVALID_PASSWORD: "Password is too weak.",
};

function formatHttpError(status: number, statusText: string, body: string): string {
  if (!body) return `HTTP ${status}: ${statusText}`;
  try {
    const parsed = JSON.parse(body);
    const detail = parsed?.detail;
    if (typeof detail === "string") {
      return FRIENDLY_ERRORS[detail] ?? detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (typeof first === "string") return first;
      if (first?.msg) return String(first.msg);
    }
  } catch {
    // not JSON — fall through
  }
  return `HTTP ${status}: ${body}`;
}

// Parses a term label string ("Spring 2026") into season and year fields
// that the backend expects. Used by classes.create and classes.update.
function parseTermLabel(term: any): {
  season: string;
  year: number;
  startsOn: string;
  endsOn: string;
} {
  const [seasonRaw, yearRaw] = term?.label?.split(" ") ?? [];
  return {
    season: seasonRaw?.toLowerCase() ?? "spring",
    year: parseInt(yearRaw) || new Date().getFullYear(),
    startsOn: term.startsOn,
    endsOn: term.endsOn,
  };
}

// ---------- Auth helpers ----------

// Posts credentials to the auth service. The response body carries the
// short-lived access token; the matching refresh-token cookie is set
// by the server (HttpOnly) and is invisible here.
async function jwtLogin(email: string, password: string): Promise<string> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    credentials: "same-origin",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(formatHttpError(res.status, res.statusText, text));
  }
  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

// Attempts to restore a session at app boot. Returns null if there is
// no valid refresh cookie, otherwise stores the new access token.
export async function bootstrapSession(): Promise<string | null> {
  return tryRefresh();
}

async function fetchMe(): Promise<User> {
  return http<User>("/users/me");
}

// ---------- API client implementation ----------

export const httpClient: ApiClient = {
  users: {
    async me() {
      // If we have no access token yet, try a one-shot refresh first.
      // The browser may still hold a valid refresh cookie from a prior
      // session even though our in-memory token was lost on reload.
      if (!tokenCache) {
        const refreshed = await tryRefresh();
        if (!refreshed) return null;
      }
      try {
        return await fetchMe();
      } catch {
        // 401 + failed refresh already cleared the token in http().
        return null;
      }
    },

    async signIn(email, password) {
      const token = await jwtLogin(email, password);
      setAuthToken(token);
      const user = await fetchMe();
      return { user, token };
    },

    async signOut() {
      // Best-effort: revoke the refresh token server-side and clear
      // the cookie. Drop the in-memory access token regardless.
      try {
        await fetch(`${BASE}/auth/logout`, {
          method: "POST",
          credentials: "same-origin",
        });
      } catch {
        // ignore
      }
      setAuthToken(null);
    },

    list: () => http("/users"),

    async register(input) {
      await http<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: input.email,
          password: input.password,
          name: input.name,
          role: input.role,
        }),
      });
      // Register does not return a token; sign in immediately to obtain one.
      const token = await jwtLogin(input.email, input.password);
      setAuthToken(token);
      const user = await fetchMe();
      return { user, token };
    },

    search: (params) => {
      const q = new URLSearchParams();
      if (params.email) q.set("email", params.email);
      if (params.name) q.set("name", params.name);
      const qs = q.toString();
      return http(`/users/search${qs ? `?${qs}` : ""}`);
    },
  },

  classes: {
    list: (opts) => {
      const q = new URLSearchParams();
      if (opts?.studentId) q.set("studentId", opts.studentId);
      if (opts?.professorId) q.set("professorId", opts.professorId);
      const qs = q.toString();
      // Enriched class catalog (with student/assignment counts) lives
      // in service-bff under /api/views/classes.
      return http(`/views/classes${qs ? `?${qs}` : ""}`);
    },

    get: (id) => http(`/views/classes/${id}`),

    create: (input) => {
      const transformed = { ...input, term: parseTermLabel(input.term) };
      return http("/classes", {
        method: "POST",
        body: JSON.stringify(transformed),
      });
    },

    update: (id, patch) => {
      const transformed = {
        ...patch,
        ...(patch.term ? { term: parseTermLabel(patch.term) } : {}),
      };
      return http(`/classes/${id}`, {
        method: "PATCH",
        body: JSON.stringify(transformed),
      });
    },

    roster: (classId) => http(`/classes/${classId}/roster`),

    addStudent: (classId, studentId) =>
      http(`/classes/${classId}/roster/${studentId}`, { method: "POST" }),

    addStudentByEmail: (classId, email) =>
      http(`/classes/${classId}/roster/by-email`, {
        method: "POST",
        body: JSON.stringify({ email }),
      }),

    removeStudent: (classId, userId) =>
      http(`/classes/${classId}/roster/${userId}`, { method: "DELETE" }),
  },

  assignments: {
    listForClass: (classId) => http(`/assignments?classId=${classId}`),

    listForStudent: (studentId) =>
      http<AssignmentForStudent[]>(`/assignments/for-student/${studentId}`),

    get: (id) => http(`/assignments/${id}`),

    create: (input) =>
      http("/assignments", {
        method: "POST",
        body: JSON.stringify(input),
      }),

    update: (id, patch) =>
      http(`/assignments/${id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      }),
  },

  submissions: {
    listForAssignment: (assignmentId) =>
      http(`/submissions?assignmentId=${assignmentId}`),

    listForStudent: (studentId) =>
      http(`/submissions?studentId=${studentId}`),

    get: (id) => http(`/submissions/${id}`),

    // Three-step upload flow:
    //   1. POST /submissions with metadata → service-submission creates the
    //      submission row and proxies presign-upload to service-file-storage.
    //      Response carries presigned PUT URLs (per file).
    //   2. Browser PUTs each file's bytes directly to MinIO. No bearer token
    //      is needed — the signature in the URL authorizes the upload.
    //   3. POST /submissions/{id}/files/confirm with the fileRefIds tells
    //      service-submission (via file-storage) to mark each FileRef as
    //      committed and returns the enriched submission.
    //
    // studentId is kept in the signature for backward compatibility with
    // existing callers but is no longer sent — the backend trusts the
    // gateway-injected identity headers instead.
    submit: async ({ assignmentId, files }) => {
      // ── Step 1: create submission + obtain presigned PUT URLs ──
      const createRes = await http<{
        id: string;
        assignmentId: string;
        studentId: string;
        files: Array<{
          fileRefId: string;
          submissionFileId: string;
          name: string;
          uploadUrl: string;
        }>;
      }>("/submissions", {
        method: "POST",
        body: JSON.stringify({
          assignmentId,
          files: files.map((f) => ({
            name: f.name,
            contentType: f.type || "application/octet-stream",
            sizeBytes: f.size,
          })),
        }),
      });

      // ── Step 2: browser → MinIO direct PUT for each file ──
      const byName = new Map(files.map((f) => [f.name, f]));
      await Promise.all(
        createRes.files.map(async (entry) => {
          const blob = byName.get(entry.name);
          if (!blob) throw new Error(`File ${entry.name} missing locally`);
          const putRes = await fetch(entry.uploadUrl, {
            method: "PUT",
            body: blob,
            headers: { "Content-Type": blob.type || "application/octet-stream" },
          });
          if (!putRes.ok) {
            throw new Error(
              `Upload to object store failed (${putRes.status}) for ${entry.name}`,
            );
          }
        }),
      );

      // ── Step 3: confirm all uploads and return enriched submission ──
      const submission = await http<unknown>(
        `/submissions/${createRes.id}/files/confirm`,
        {
          method: "POST",
          body: JSON.stringify({
            fileRefIds: createRes.files.map((f) => f.fileRefId),
          }),
        },
      );
      return submission as Submission;
    },
  },

  grading: {
    upsertGrade: (input) =>
      http("/grading", { method: "POST", body: JSON.stringify(input) }),

    listForStudent: (studentId) => http(`/grading?studentId=${studentId}`),

    studentStats: (studentId) =>
      http<StudentStats>(`/students/${studentId}/stats`),

    professorStats: (professorId) =>
      http<ProfessorStats>(`/professors/${professorId}/stats`),

    gradingQueue: (professorId, limit) => {
      const qs = limit ? `?limit=${limit}` : "";
      return http<GradingQueueItem[]>(
        `/professors/${professorId}/grading-queue${qs}`,
      );
    },
  },
};

export type { AuthSession };
