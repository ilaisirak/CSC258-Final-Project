// Domain types — mirror the planned microservice boundaries so backend services
// can implement these contracts directly. Keep these flat & serializable.

export type Role = "student" | "professor";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  avatarUrl?: string;
}

export interface ClassTerm {
  /** e.g. "Spring 2026" */
  label: string;
  startsOn: string; // ISO date
  endsOn: string; // ISO date
}

export interface Class {
  id: string;
  code: string; // e.g. "CSC258"
  name: string; // e.g. "Software Engineering"
  description?: string;
  professorId: string;
  professorName: string;
  term: ClassTerm;
  /** denormalized counts; backend may compute lazily */
  studentCount: number;
  assignmentCount: number;
}

export interface Enrollment {
  classId: string;
  userId: string;
  enrolledAt: string;
}

export type AssignmentStatus = "draft" | "open" | "closed";

export interface Assignment {
  id: string;
  classId: string;
  title: string;
  description: string;
  dueAt: string; // ISO
  pointsPossible: number;
  status: AssignmentStatus;
  attachments?: FileRef[];
  allowResubmission: boolean;
}

export interface FileRef {
  id: string;
  name: string;
  sizeBytes: number;
  contentType: string;
  url?: string; // signed URL or path
}

export type SubmissionStatus = "submitted" | "graded" | "returned";

export interface Submission {
  id: string;
  assignmentId: string;
  studentId: string;
  studentName: string;
  submittedAt: string;
  status: SubmissionStatus;
  files: FileRef[];
  /** present once graded */
  grade?: Grade;
}

export interface Grade {
  id: string;
  submissionId: string;
  score: number; // 0..pointsPossible
  pointsPossible: number;
  feedback?: string;
  gradedById: string;
  gradedAt: string;
}

/** Per-student computed view used by dashboards. */
export interface AssignmentForStudent {
  assignment: Assignment;
  className: string;
  classCode: string;
  submission?: Submission;
}

export interface ApiError {
  message: string;
  code?: string;
}
