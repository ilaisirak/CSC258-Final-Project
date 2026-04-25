import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppShell } from "@/components/layout";
import { RequireAuth, RequireRole, RoleHome } from "./guards";
import { LoginPage } from "@/pages/Login";
import { NotFoundPage } from "@/pages/NotFound";
import { SettingsPage } from "@/pages/Settings";
import { StudentDashboardPage } from "@/pages/student/Dashboard";
import { StudentClassesPage } from "@/pages/student/Classes";
import { StudentClassDetailPage } from "@/pages/student/ClassDetail";
import { StudentAssignmentsPage } from "@/pages/student/Assignments";
import { StudentAssignmentDetailPage } from "@/pages/student/AssignmentDetail";
import { StudentGradesPage } from "@/pages/student/Grades";
import { ProfessorDashboardPage } from "@/pages/professor/Dashboard";
import { ProfessorClassesPage } from "@/pages/professor/Classes";
import { ProfessorClassDetailPage } from "@/pages/professor/ClassDetail";
import { ProfessorClassNewPage } from "@/pages/professor/ClassNew";
import { ProfessorGradingQueuePage } from "@/pages/professor/GradingQueue";
import { ProfessorGradingPage } from "@/pages/professor/Grading";
import { ProfessorRosterPage } from "@/pages/professor/Roster";

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/", element: <RoleHome /> },
  {
    path: "/student",
    element: (
      <RequireRole role="student">
        <AppShell />
      </RequireRole>
    ),
    children: [
      { index: true, element: <StudentDashboardPage /> },
      { path: "classes", element: <StudentClassesPage /> },
      { path: "classes/:classId", element: <StudentClassDetailPage /> },
      { path: "assignments", element: <StudentAssignmentsPage /> },
      { path: "assignments/:assignmentId", element: <StudentAssignmentDetailPage /> },
      { path: "grades", element: <StudentGradesPage /> },
    ],
  },
  {
    path: "/professor",
    element: (
      <RequireRole role="professor">
        <AppShell />
      </RequireRole>
    ),
    children: [
      { index: true, element: <ProfessorDashboardPage /> },
      { path: "classes", element: <ProfessorClassesPage /> },
      { path: "classes/new", element: <ProfessorClassNewPage /> },
      { path: "classes/:classId", element: <ProfessorClassDetailPage /> },
      {
        path: "classes/:classId/assignments/:assignmentId/grade",
        element: <ProfessorGradingPage />,
      },
      { path: "grading", element: <ProfessorGradingQueuePage /> },
      { path: "roster", element: <ProfessorRosterPage /> },
    ],
  },
  {
    path: "/settings",
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [{ index: true, element: <SettingsPage /> }],
  },
  { path: "*", element: <NotFoundPage /> },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
