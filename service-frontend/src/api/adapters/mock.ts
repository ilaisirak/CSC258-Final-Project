import type {
  Assignment,
  AssignmentForStudent,
  Class,
  FileRef,
  Grade,
  Role,
  Submission,
} from "../types";
import {
  seedAssignments,
  seedClasses,
  seedEnrollments,
  seedSubmissions,
  seedUsers,
} from "../fixtures";
import type {
  ApiClient,
  AssignmentsAdapter,
  ClassesAdapter,
  GradingAdapter,
  SubmissionsAdapter,
  UsersAdapter,
} from "./interfaces";

// In-memory store. Module-level so state persists across page navigations.
const store = {
  users: [...seedUsers],
  classes: [...seedClasses],
  enrollments: [...seedEnrollments],
  assignments: [...seedAssignments],
  submissions: [...seedSubmissions],
  currentUserId: null as string | null,
};

const SESSION_KEY = "gradingPortal.session";

// Restore current user from localStorage on module load.
try {
  const raw = typeof window !== "undefined" ? window.localStorage.getItem(SESSION_KEY) : null;
  if (raw) {
    const parsed = JSON.parse(raw) as { userId: string };
    if (store.users.some((u) => u.id === parsed.userId)) {
      store.currentUserId = parsed.userId;
    }
  }
} catch {
  // ignore
}

const delay = (ms = 250) => new Promise<void>((r) => setTimeout(r, ms));
const id = (prefix: string) => `${prefix}-${Math.random().toString(36).slice(2, 9)}`;

const usersAdapter: UsersAdapter = {
  async me() {
    await delay(100);
    return store.users.find((u) => u.id === store.currentUserId) ?? null;
  },
  async signIn(role: Role, name: string) {
    await delay();
    const trimmed = name.trim() || (role === "student" ? "Alex Chen" : "Dr. Mira Patel");
    // Reuse a seeded user with the same role+name when possible.
    let user = store.users.find(
      (u) => u.role === role && u.name.toLowerCase() === trimmed.toLowerCase(),
    );
    if (!user) {
      user = {
        id: id("u"),
        name: trimmed,
        email: `${trimmed.toLowerCase().replace(/\s+/g, ".")}@example.edu`,
        role,
      };
      store.users.push(user);
      if (role === "student") {
        store.enrollments.push({
          classId: "c-1",
          userId: user.id,
          enrolledAt: new Date().toISOString(),
        });
      }
    }
    store.currentUserId = user.id;
    window.localStorage.setItem(SESSION_KEY, JSON.stringify({ userId: user.id }));
    return user;
  },
  async signOut() {
    await delay(100);
    store.currentUserId = null;
    window.localStorage.removeItem(SESSION_KEY);
  },
  async list() {
    await delay();
    return [...store.users];
  },
  async createUser(input) {
    await delay();
    const existing = store.users.find(
      (u) => u.email.toLowerCase() === input.email.toLowerCase(),
    );
    if (existing) {
      throw new Error("A user with that email already exists");
    }
    const newUser = {
      id: id("u"),
      name: input.name,
      email: input.email,
      role: input.role,
    };
    store.users.push(newUser);
    if (newUser.role === "student") {
      store.enrollments.push({
        classId: "c-1",
        userId: newUser.id,
        enrolledAt: new Date().toISOString(),
      });
    }
    return newUser;
  },
  async search(params: { email?: string; name?: string }) {
    await delay(100);
    let result = [...store.users];
    if (params.email) {
      result = result.filter((u) => u.email.toLowerCase() === params.email!.toLowerCase());
    } else if (params.name) {
      result = result.filter((u) => u.name.toLowerCase().includes(params.name!.toLowerCase()));
    }
    return result;
  },
  };

const classesAdapter: ClassesAdapter = {
  async list(opts) {
    await delay();
    if (opts?.professorId) {
      return store.classes.filter((c) => c.professorId === opts.professorId);
    }
    if (opts?.studentId) {
      const ids = store.enrollments
        .filter((e) => e.userId === opts.studentId)
        .map((e) => e.classId);
      return store.classes.filter((c) => ids.includes(c.id));
    }
    return [...store.classes];
  },
  async get(classId: string) {
    await delay();
    const c = store.classes.find((x) => x.id === classId);
    if (!c) throw new Error("Class not found");
    return c;
  },
  async create(input) {
    await delay();
    const created: Class = { ...input, id: id("c"), studentCount: 0, assignmentCount: 0 };
    store.classes.push(created);
    return created;
  },
  async update(classId, patch) {
    await delay();
    const idx = store.classes.findIndex((c) => c.id === classId);
    if (idx === -1) throw new Error("Class not found");
    store.classes[idx] = { ...store.classes[idx], ...patch };
    return store.classes[idx];
  },
  async roster(classId: string) {
    await delay();
    const userIds = store.enrollments.filter((e) => e.classId === classId).map((e) => e.userId);
    return store.users.filter((u) => userIds.includes(u.id));
  },
  async addStudent(classId, email) {
    await delay();
    let user = store.users.find((u) => u.email.toLowerCase() === email.toLowerCase());
    if (!user) {
      const name = email
        .split("@")[0]
        .split(/[._-]/)
        .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
        .join(" ");
      user = { id: id("u"), name, email, role: "student" };
      store.users.push(user);
    }
    if (!store.enrollments.some((e) => e.classId === classId && e.userId === user!.id)) {
      store.enrollments.push({
        classId,
        userId: user.id,
        enrolledAt: new Date().toISOString(),
      });
      const cls = store.classes.find((c) => c.id === classId);
      if (cls) cls.studentCount += 1;
    }
    return user;
  },
  async removeStudent(classId, userId) {
    await delay();
    const before = store.enrollments.length;
    store.enrollments = store.enrollments.filter(
      (e) => !(e.classId === classId && e.userId === userId),
    );
    if (store.enrollments.length < before) {
      const cls = store.classes.find((c) => c.id === classId);
      if (cls) cls.studentCount = Math.max(0, cls.studentCount - 1);
    }
  },
};

const assignmentsAdapter: AssignmentsAdapter = {
  async listForClass(classId: string) {
    await delay();
    return store.assignments.filter((a) => a.classId === classId);
  },
  async listForStudent(studentId: string) {
    await delay();
    const classIds = store.enrollments
      .filter((e) => e.userId === studentId)
      .map((e) => e.classId);
    const result: AssignmentForStudent[] = [];
    for (const a of store.assignments) {
      if (!classIds.includes(a.classId)) continue;
      const cls = store.classes.find((c) => c.id === a.classId);
      if (!cls) continue;
      const submission = store.submissions.find(
        (s) => s.assignmentId === a.id && s.studentId === studentId,
      );
      result.push({
        assignment: a,
        className: cls.name,
        classCode: cls.code,
        submission,
      });
    }
    return result;
  },
  async get(assignmentId: string) {
    await delay();
    const a = store.assignments.find((x) => x.id === assignmentId);
    if (!a) throw new Error("Assignment not found");
    return a;
  },
  async create(input) {
    await delay();
    const created: Assignment = { ...input, id: id("a") };
    store.assignments.push(created);
    const cls = store.classes.find((c) => c.id === created.classId);
    if (cls) cls.assignmentCount += 1;
    return created;
  },
  async update(assignmentId, patch) {
    await delay();
    const idx = store.assignments.findIndex((a) => a.id === assignmentId);
    if (idx === -1) throw new Error("Assignment not found");
    store.assignments[idx] = { ...store.assignments[idx], ...patch };
    return store.assignments[idx];
  },
};

const submissionsAdapter: SubmissionsAdapter = {
  async listForAssignment(assignmentId: string) {
    await delay();
    return store.submissions.filter((s) => s.assignmentId === assignmentId);
  },
  async listForStudent(studentId: string) {
    await delay();
    return store.submissions.filter((s) => s.studentId === studentId);
  },
  async get(submissionId: string) {
    await delay();
    const s = store.submissions.find((x) => x.id === submissionId);
    if (!s) throw new Error("Submission not found");
    return s;
  },
  async submit({ assignmentId, studentId, studentName, files }) {
    await delay(600);
    const student = store.users.find((u) => u.id === studentId);
    const fileRefs: FileRef[] = files.map((f) => ({
      id: id("f"),
      name: f.name,
      sizeBytes: f.size,
      contentType: f.type || "application/octet-stream",
    }));
    const submission: Submission = {
      id: id("s"),
      assignmentId,
      studentId,
      studentName: studentName ?? student?.name ?? "Unknown",
      submittedAt: new Date().toISOString(),
      status: "submitted",
      files: fileRefs,
    };
    store.submissions.push(submission);
    return submission;
  },
};

const gradingAdapter: GradingAdapter = {
  async upsertGrade(input) {
    await delay();
    const submission = store.submissions.find((s) => s.id === input.submissionId);
    if (!submission) throw new Error("Submission not found");
    const grade: Grade = {
      id: submission.grade?.id ?? id("g"),
      submissionId: input.submissionId,
      score: input.score,
      pointsPossible: input.pointsPossible,
      feedback: input.feedback,
      gradedById: input.gradedById,
      gradedAt: new Date().toISOString(),
    };
    submission.grade = grade;
    submission.status = "graded";
    return grade;
  },
  async listForStudent(studentId: string) {
    await delay();
    return store.submissions
      .filter((s) => s.studentId === studentId && s.grade)
      .map((s) => s.grade as Grade);
  },
};

export const mockClient: ApiClient = {
  users: usersAdapter,
  classes: classesAdapter,
  assignments: assignmentsAdapter,
  submissions: submissionsAdapter,
  grading: gradingAdapter,
};

// Exposed for debugging in the console; harmless in production.
if (typeof window !== "undefined") {
  (window as unknown as { __gpStore?: typeof store }).__gpStore = store;
}