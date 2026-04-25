// HTTP adapter — a thin sketch matching the planned ingress paths. It is NOT used
// by default; the mock adapter handles everything until backends are ready. Each
// namespace can be flipped to HTTP individually via env (see client.ts).
//
// Conventions:
//   GET    /api/users/me
//   POST   /api/users/sign-in
//   GET    /api/classes?studentId=... | ?professorId=...
//   GET    /api/classes/:id
//   POST   /api/classes
//   GET    /api/classes/:id/roster
//   GET    /api/assignments?classId=...
//   GET    /api/assignments/:id
//   POST   /api/assignments
//   GET    /api/submissions?assignmentId=... | ?studentId=...
//   POST   /api/submit                    (existing service-submission contract)
//   POST   /api/grading
//
// The real backend services can adjust these paths; only this file changes.

import type { Submission } from "../types";
import type { ApiClient } from "./interfaces";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

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
  return (await res.json()) as T;
}

export const httpClient: ApiClient = {
  users: {
    me: () => http("/users/me"),
    signIn: (role, name) =>
      http("/users/sign-in", { method: "POST", body: JSON.stringify({ role, name }) }),
    signOut: () => http("/users/sign-out", { method: "POST" }),
    list: () => http("/users"),
  },
  classes: {
    list: (opts) => {
      const q = new URLSearchParams();
      if (opts?.studentId) q.set("studentId", opts.studentId);
      if (opts?.professorId) q.set("professorId", opts.professorId);
      const qs = q.toString();
      return http(`/classes${qs ? `?${qs}` : ""}`);
    },
    get: (id) => http(`/classes/${id}`),
    create: (input) => http("/classes", { method: "POST", body: JSON.stringify(input) }),
    update: (id, patch) => http(`/classes/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
    roster: (classId) => http(`/classes/${classId}/roster`),
    addStudent: (classId, email) =>
      http(`/classes/${classId}/roster`, {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    removeStudent: (classId, userId) =>
      http(`/classes/${classId}/roster/${userId}`, { method: "DELETE" }),
  },
  assignments: {
    listForClass: (classId) => http(`/assignments?classId=${classId}`),
    listForStudent: (studentId) => http(`/assignments?studentId=${studentId}`),
    get: (id) => http(`/assignments/${id}`),
    create: (input) => http("/assignments", { method: "POST", body: JSON.stringify(input) }),
    update: (id, patch) =>
      http(`/assignments/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  },
  submissions: {
    listForAssignment: (assignmentId) => http(`/submissions?assignmentId=${assignmentId}`),
    listForStudent: (studentId) => http(`/submissions?studentId=${studentId}`),
    get: (id) => http(`/submissions/${id}`),
    submit: async ({ assignmentId, studentId, files }) => {
      // Existing /submit endpoint accepts multipart form data.
      const fd = new FormData();
      fd.append("assignmentId", assignmentId);
      fd.append("studentId", studentId);
      for (const f of files) fd.append("file", f, f.name);
      const res = await fetch(`${BASE}/submit`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as Submission;
    },
  },
  grading: {
    upsertGrade: (input) => http("/grading", { method: "POST", body: JSON.stringify(input) }),
    listForStudent: (studentId) => http(`/grading?studentId=${studentId}`),
  },
};
