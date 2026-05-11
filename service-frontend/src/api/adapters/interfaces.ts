import type {
  Assignment,
  AssignmentForStudent,
  Class,
  Grade,
  GradingQueueItem,
  ProfessorStats,
  Role,
  StudentStats,
  Submission,
  User,
} from "../types";

export interface AuthSession {
  user: User;
  token: string;
}

export interface UsersAdapter {
  /** Returns the currently signed-in user, or null if no valid session. */
  me(): Promise<User | null>;
  /** Authenticate with email + password. Returns the user and JWT. */
  signIn(email: string, password: string): Promise<AuthSession>;
  /** Clear the current session. */
  signOut(): Promise<void>;
  list(): Promise<User[]>;
  /** Register a new account; returns the user and JWT for the new account. */
  register(input: {
    name: string;
    email: string;
    password: string;
    role: Role;
  }): Promise<AuthSession>;
  search(params: { email?: string; name?: string }): Promise<User[]>;
}

export interface ClassesAdapter {
  list(opts?: { professorId?: string; studentId?: string }): Promise<Class[]>;
  get(id: string): Promise<Class>;
  create(input: Omit<Class, "id" | "studentCount" | "assignmentCount">): Promise<Class>;
  update(id: string, patch: Partial<Class>): Promise<Class>;
  roster(classId: string): Promise<User[]>;
  addStudent(classId: string, studentId: string): Promise<User>;
  /** One-call email enrollment: backend resolves email→UUID and enrolls. */
  addStudentByEmail(classId: string, email: string): Promise<User>;
  removeStudent(classId: string, userId: string): Promise<void>;
}

export interface AssignmentsAdapter {
  listForClass(classId: string): Promise<Assignment[]>;
  listForStudent(studentId: string): Promise<AssignmentForStudent[]>;
  get(id: string): Promise<Assignment>;
  create(input: Omit<Assignment, "id">): Promise<Assignment>;
  update(id: string, patch: Partial<Assignment>): Promise<Assignment>;
}

export interface SubmissionsAdapter {
  listForAssignment(assignmentId: string): Promise<Submission[]>;
  listForStudent(studentId: string): Promise<Submission[]>;
  get(id: string): Promise<Submission>;
  submit(input: { assignmentId: string; studentId: string; files: File[] }): Promise<Submission>;
}

export interface GradingAdapter {
  upsertGrade(input: {
    submissionId: string;
    score: number;
    pointsPossible: number;
    feedback?: string;
  }): Promise<Grade>;
  listForStudent(studentId: string): Promise<Grade[]>;
  /** Aggregated student dashboard stats. */
  studentStats(studentId: string): Promise<StudentStats>;
  /** Aggregated professor dashboard stats. */
  professorStats(professorId: string): Promise<ProfessorStats>;
  /** Pre-joined queue of ungraded submissions across the professor's classes. */
  gradingQueue(professorId: string, limit?: number): Promise<GradingQueueItem[]>;
}

export interface ApiClient {
  users: UsersAdapter;
  classes: ClassesAdapter;
  assignments: AssignmentsAdapter;
  submissions: SubmissionsAdapter;
  grading: GradingAdapter;
}
