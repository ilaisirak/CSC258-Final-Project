import type {
  Assignment,
  Class,
  Grade,
  Submission,
  User,
} from "./types";

const now = new Date();
const days = (n: number) => {
  const d = new Date(now);
  d.setDate(d.getDate() + n);
  return d.toISOString();
};

export const seedUsers: User[] = [
  {
    id: "u-prof-1",
    name: "Dr. Mira Patel",
    email: "mira.patel@example.edu",
    role: "professor",
  },
  {
    id: "u-stu-1",
    name: "Alex Chen",
    email: "alex.chen@example.edu",
    role: "student",
  },
  {
    id: "u-stu-2",
    name: "Jordan Kim",
    email: "jordan.kim@example.edu",
    role: "student",
  },
  {
    id: "u-stu-3",
    name: "Sam Rivera",
    email: "sam.rivera@example.edu",
    role: "student",
  },
];

export const seedClasses: Class[] = [
  {
    id: "c-1",
    code: "CSC258",
    name: "Software Engineering",
    description:
      "Principles of large-scale software development: architecture, microservices, testing, and deployment.",
    professorId: "u-prof-1",
    professorName: "Dr. Mira Patel",
    term: { label: "Spring 2026", startsOn: "2026-01-12", endsOn: "2026-05-08" },
    studentCount: 28,
    assignmentCount: 4,
  },
  {
    id: "c-2",
    code: "CSC340",
    name: "Distributed Systems",
    description:
      "Foundations of distributed computing: consistency models, consensus, fault tolerance, and cloud-native design.",
    professorId: "u-prof-1",
    professorName: "Dr. Mira Patel",
    term: { label: "Spring 2026", startsOn: "2026-01-12", endsOn: "2026-05-08" },
    studentCount: 22,
    assignmentCount: 3,
  },
  {
    id: "c-3",
    code: "CSC210",
    name: "Data Structures",
    description: "Core data structures and algorithm analysis.",
    professorId: "u-prof-1",
    professorName: "Dr. Mira Patel",
    term: { label: "Spring 2026", startsOn: "2026-01-12", endsOn: "2026-05-08" },
    studentCount: 41,
    assignmentCount: 2,
  },
];

export const seedEnrollments = [
  { classId: "c-1", userId: "u-stu-1", enrolledAt: days(-90) },
  { classId: "c-2", userId: "u-stu-1", enrolledAt: days(-90) },
  { classId: "c-3", userId: "u-stu-1", enrolledAt: days(-90) },
  { classId: "c-1", userId: "u-stu-2", enrolledAt: days(-90) },
  { classId: "c-1", userId: "u-stu-3", enrolledAt: days(-90) },
  { classId: "c-2", userId: "u-stu-2", enrolledAt: days(-90) },
];

export const seedAssignments: Assignment[] = [
  {
    id: "a-1",
    classId: "c-1",
    title: "Microservices design proposal",
    description:
      "Submit a 2-page proposal outlining the architecture of your group's grading portal: services, data ownership, and deployment topology.",
    dueAt: days(3),
    pointsPossible: 100,
    status: "open",
    allowResubmission: true,
  },
  {
    id: "a-2",
    classId: "c-1",
    title: "Service implementation: Submission",
    description:
      "Implement the Submission service with file upload to MinIO/GCS. Include a Dockerfile and a Kubernetes manifest.",
    dueAt: days(10),
    pointsPossible: 100,
    status: "open",
    allowResubmission: true,
  },
  {
    id: "a-3",
    classId: "c-1",
    title: "Reading response: CAP theorem",
    description: "1-page reflection on Brewer's CAP theorem and its practical implications.",
    dueAt: days(-2),
    pointsPossible: 50,
    status: "closed",
    allowResubmission: false,
  },
  {
    id: "a-4",
    classId: "c-1",
    title: "Final project — checkpoint 1",
    description: "Demo of running services and a brief write-up of progress.",
    dueAt: days(21),
    pointsPossible: 150,
    status: "open",
    allowResubmission: true,
  },
  {
    id: "a-5",
    classId: "c-2",
    title: "Raft implementation",
    description: "Implement leader election from the Raft paper in a language of your choice.",
    dueAt: days(7),
    pointsPossible: 100,
    status: "open",
    allowResubmission: true,
  },
  {
    id: "a-6",
    classId: "c-3",
    title: "Hash table benchmarks",
    description: "Compare open addressing vs. chaining across realistic workloads.",
    dueAt: days(-5),
    pointsPossible: 80,
    status: "closed",
    allowResubmission: false,
  },
];

export const seedSubmissions: Submission[] = [
  {
    id: "s-1",
    assignmentId: "a-3",
    studentId: "u-stu-1",
    studentName: "Alex Chen",
    submittedAt: days(-3),
    status: "graded",
    files: [
      {
        id: "f-1",
        name: "cap-reflection.pdf",
        sizeBytes: 184320,
        contentType: "application/pdf",
      },
    ],
    grade: {
      id: "g-1",
      submissionId: "s-1",
      score: 46,
      pointsPossible: 50,
      feedback: "Strong analysis. Tighten the conclusion and cite Gilbert & Lynch.",
      gradedById: "u-prof-1",
      gradedAt: days(-1),
    },
  },
  {
    id: "s-2",
    assignmentId: "a-6",
    studentId: "u-stu-1",
    studentName: "Alex Chen",
    submittedAt: days(-6),
    status: "graded",
    files: [
      { id: "f-2", name: "hashbench.zip", sizeBytes: 2_400_000, contentType: "application/zip" },
    ],
    grade: {
      id: "g-2",
      submissionId: "s-2",
      score: 72,
      pointsPossible: 80,
      feedback: "Good methodology; missing a couple of edge cases in the chaining benchmarks.",
      gradedById: "u-prof-1",
      gradedAt: days(-4),
    },
  },
  {
    id: "s-3",
    assignmentId: "a-3",
    studentId: "u-stu-2",
    studentName: "Jordan Kim",
    submittedAt: days(-2),
    status: "submitted",
    files: [
      { id: "f-3", name: "reflection.pdf", sizeBytes: 156000, contentType: "application/pdf" },
    ],
  },
  {
    id: "s-4",
    assignmentId: "a-3",
    studentId: "u-stu-3",
    studentName: "Sam Rivera",
    submittedAt: days(-2),
    status: "submitted",
    files: [
      { id: "f-4", name: "cap.pdf", sizeBytes: 201000, contentType: "application/pdf" },
    ],
  },
];

export const seedGrades: Grade[] = seedSubmissions
  .map((s) => s.grade)
  .filter((g): g is Grade => Boolean(g));
