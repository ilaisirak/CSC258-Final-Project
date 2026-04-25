import type {
  Assignment,
  AssignmentForStudent,
  Class,
  Grade,
  Role,
  Submission,
  User,
} from "../types";

export interface UsersAdapter {
  me(): Promise<User | null>;
  signIn(role: Role, name: string): Promise<User>;
  signOut(): Promise<void>;
  list(): Promise<User[]>;
}

export interface ClassesAdapter {
  list(opts?: { professorId?: string; studentId?: string }): Promise<Class[]>;
  get(id: string): Promise<Class>;
  create(input: Omit<Class, "id" | "studentCount" | "assignmentCount">): Promise<Class>;
  update(id: string, patch: Partial<Class>): Promise<Class>;
  roster(classId: string): Promise<User[]>;
  addStudent(classId: string, email: string): Promise<User>;
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
    gradedById: string;
  }): Promise<Grade>;
  listForStudent(studentId: string): Promise<Grade[]>;
}

export interface ApiClient {
  users: UsersAdapter;
  classes: ClassesAdapter;
  assignments: AssignmentsAdapter;
  submissions: SubmissionsAdapter;
  grading: GradingAdapter;
}
