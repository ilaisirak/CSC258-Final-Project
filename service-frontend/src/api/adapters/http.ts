// http.ts
// HTTP adapter — maps the ApiClient interface to real backend endpoints.
// Each namespace can be enabled independently via env vars (see client.ts).
//
// Conventions:
//   GET    /api/users/me
//   POST   /api/users/sign-in
//   GET    /api/classes?studentId=... | ?professorId=...
//   GET    /api/classes/:id
//   POST   /api/classes
//   GET    /api/classes/:id/roster
//   POST   /api/classes/:id/roster/:studentId
//   DELETE /api/classes/:id/roster/:userId
//   GET    /api/assignments?classId=...
//   GET    /api/assignments/:id
//   POST   /api/assignments
//   GET    /api/submissions?assignmentId=... | ?studentId=...
//   POST   /api/submit                    (multipart form data)
//   POST   /api/grading
//   GET    /api/grading?studentId=...

import type { Assignment, Class, Submission } from "../types";
import type { ApiClient } from "./interfaces";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

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
      {} as Record<string, unknown>
    );
  }
  return input;
}

// ---------- Generic HTTP fetch wrapper ----------

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${body || res.statusText}`);
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  const data = await res.json();
  return keysToCamelCase(data) as T; // ← all responses now converted
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

// ---------- API client implementation ----------

export const httpClient: ApiClient = {
  users: {
    // Restores session on page load by reading X-User-Id header.
    // Returns null if no session exists — AuthContext treats this as unauthenticated.
    me: () => http("/users/me"),

    // Signs in by name and role — matches backend UserSignIn schema.
    signIn: (role, name) =>
      http("/users/sign-in", {
        method: "POST",
        body: JSON.stringify({ role, name }),
      }),

    signOut: () => http("/users/sign-out", { method: "POST" }),

    list: () => http("/users"),

    createUser: (input) =>
      http("/users", {
        method: "POST",
        body: JSON.stringify(input), 
      }),

    search: (params) => {
      const q = new URLSearchParams();
      if (params.email) q.set("email", params.email);
      if (params.name) q.set("name", params.name);
      const qs = q.toString();
      return http(`/users/search${qs ? `?${qs}` : ""}`);
    },
  },

  classes: {
    // Accepts studentId or professorId — backend handles camelCase
    // query params via route aliases.
    list: (opts) => {
      const q = new URLSearchParams();
      if (opts?.studentId) q.set("studentId", opts.studentId);
      if (opts?.professorId) q.set("professorId", opts.professorId);
      const qs = q.toString();
      return http(`/classes${qs ? `?${qs}` : ""}`);
    },

    get: (id) => http(`/classes/${id}`),

    // The frontend sends term.label ("Spring 2026") but the backend expects
    // term.season and term.year as separate fields. parseTermLabel handles
    // this transformation so neither the form nor the backend needs to change.
    create: (input) => {
      const transformed = {
        ...input,
        term: parseTermLabel(input.term),
      };
      return http("/classes", {
        method: "POST",
        body: JSON.stringify(transformed),
      });
    },

    // Same term transformation as create — patch may include a term object.
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

    // Updated to use path parameter instead of request body.
    addStudent: (classId, studentId) =>
      http(`/classes/${classId}/roster/${studentId}`, { method: "POST" }),

    removeStudent: (classId, userId) =>
      http(`/classes/${classId}/roster/${userId}`, { method: "DELETE" }),
  },

  assignments: {
    listForClass: (classId) => http(`/assignments?classId=${classId}`),

    // Assembles AssignmentForStudent[] on the frontend by fetching classes,
    // assignments, and submissions in parallel then joining them.
    // This avoids adding cross-service calls to the backend.
    listForStudent: async (studentId) => {
      // Fetch enrolled classes and submissions in parallel
      const [classes, submissions] = await Promise.all([
        http<Class[]>(`/classes?studentId=${studentId}`),
        http<Submission[]>(`/submissions?studentId=${studentId}`),
      ]);

      // Fetch assignments for all enrolled classes in parallel
      const arrays = await Promise.all(
        classes.map((c) => http<Assignment[]>(`/assignments?classId=${c.id}`))
      );
      const assignments = arrays.flat();

      // Assemble the AssignmentForStudent shape the frontend expects
      return assignments.map((a) => {
        const cls = classes.find((c) => c.id === a.classId);
        const submission = submissions.find((s) => s.assignmentId === a.id);
        return {
          assignment: a,
          className: cls?.name ?? "",
          classCode: cls?.code ?? "",
          submission,
        };
      });
    },

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

    // Sends multipart form data to the submission service.
    // Content-Type is intentionally omitted so fetch sets the
    // multipart boundary automatically from the FormData object.
    submit: async ({ assignmentId, studentId, studentName, files }) => {
      const fd = new FormData();
      fd.append("assignmentId", assignmentId);
      fd.append("studentId", studentId);
      fd.append("studentName", studentName); // ← added
      for (const f of files) fd.append("file", f, f.name);

      const res = await fetch(`${BASE}/submit`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return keysToCamelCase(data) as Submission;
    },
  },

  grading: {
    upsertGrade: (input) =>
      http("/grading", { method: "POST", body: JSON.stringify(input) }),

    listForStudent: (studentId) =>
      http(`/grading?studentId=${studentId}`),
  },
};