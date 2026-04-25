import { useMemo } from "react";
import { Link } from "react-router-dom";
import { CalendarClock, GraduationCap, BookOpen } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Card, EmptyState, Skeleton } from "@/components/ui";
import { ClassCard } from "@/components/domain/ClassCard";
import { AssignmentRow } from "@/components/domain/AssignmentRow";
import { StatCard } from "@/components/domain/StatCard";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import { gradePercent } from "@/lib/format";
import layouts from "@/styles/layouts.module.css";

export function StudentDashboardPage() {
  const { user } = useAuth();
  const studentId = user!.id;

  const classesQ = useQuery(() => api.classes.list({ studentId }), [studentId]);
  const assignsQ = useQuery(() => api.assignments.listForStudent(studentId), [studentId]);

  const upcoming = useMemo(() => {
    if (!assignsQ.data) return [];
    const now = Date.now();
    return [...assignsQ.data]
      .filter((x) => new Date(x.assignment.dueAt).getTime() >= now)
      .sort(
        (a, b) =>
          new Date(a.assignment.dueAt).getTime() - new Date(b.assignment.dueAt).getTime(),
      )
      .slice(0, 4);
  }, [assignsQ.data]);

  const recentGrades = useMemo(() => {
    if (!assignsQ.data) return [];
    return assignsQ.data
      .filter((x) => x.submission?.grade)
      .sort(
        (a, b) =>
          new Date(b.submission!.grade!.gradedAt).getTime() -
          new Date(a.submission!.grade!.gradedAt).getTime(),
      )
      .slice(0, 4);
  }, [assignsQ.data]);

  const avgPct = useMemo(() => {
    const graded = (assignsQ.data ?? []).filter((x) => x.submission?.grade);
    if (graded.length === 0) return null;
    const sum = graded.reduce(
      (acc, x) => acc + gradePercent(x.submission!.grade!.score, x.submission!.grade!.pointsPossible),
      0,
    );
    return Math.round(sum / graded.length);
  }, [assignsQ.data]);

  return (
    <PageContainer>
      <PageHeader
        eyebrow={greeting()}
        title={`Welcome back, ${user!.name.split(" ")[0]}`}
        description="Here’s a quick look at what’s due, your classes, and recent feedback."
      />

      <div className={layouts.statGrid}>
        <StatCard
          label="Classes"
          value={classesQ.data?.length ?? "—"}
          icon={<BookOpen size={18} />}
          tone="accent"
        />
        <StatCard
          label="Upcoming"
          value={upcoming.length}
          icon={<CalendarClock size={18} />}
          tone="warning"
          hint={upcoming[0] ? `Next: ${upcoming[0].assignment.title}` : undefined}
        />
        <StatCard
          label="Average grade"
          value={avgPct === null ? "—" : `${avgPct}%`}
          icon={<GraduationCap size={18} />}
          tone="success"
          hint={avgPct === null ? "No graded work yet" : `Across ${recentGrades.length} graded`}
        />
      </div>

      <section className={layouts.section}>
        <div className={layouts.sectionHeading}>
          <h2 className={layouts.sectionTitle}>Upcoming</h2>
          <Link to="/student/assignments" className={layouts.sectionAction}>
            View all
          </Link>
        </div>
        {assignsQ.loading ? (
          <ListSkeleton />
        ) : upcoming.length === 0 ? (
          <EmptyState
            icon={<CalendarClock />}
            title="Nothing due right now"
            description="When your professors post new assignments, they’ll show up here."
          />
        ) : (
          <div className={layouts.list}>
            {upcoming.map((x) => (
              <AssignmentRow
                key={x.assignment.id}
                assignment={x.assignment}
                classCode={x.classCode}
                className={x.className}
                submission={x.submission}
                to={`/student/assignments/${x.assignment.id}`}
              />
            ))}
          </div>
        )}
      </section>

      <section className={layouts.section}>
        <div className={layouts.sectionHeading}>
          <h2 className={layouts.sectionTitle}>Your classes</h2>
          <Link to="/student/classes" className={layouts.sectionAction}>
            View all
          </Link>
        </div>
        {classesQ.loading ? (
          <CardGridSkeleton />
        ) : (classesQ.data?.length ?? 0) === 0 ? (
          <EmptyState
            icon={<BookOpen />}
            title="No classes yet"
            description="Once you’re enrolled in a class, it’ll appear here."
          />
        ) : (
          <div className={layouts.grid}>
            {classesQ.data!.map((c) => (
              <ClassCard key={c.id} cls={c} to={`/student/classes/${c.id}`} />
            ))}
          </div>
        )}
      </section>

      <section className={layouts.section}>
        <h2 className={layouts.sectionTitle}>Recent grades</h2>
        {assignsQ.loading ? (
          <ListSkeleton />
        ) : recentGrades.length === 0 ? (
          <EmptyState
            icon={<GraduationCap />}
            title="No grades yet"
            description="When your work is graded, the latest results will land here."
          />
        ) : (
          <div className={layouts.list}>
            {recentGrades.map((x) => (
              <AssignmentRow
                key={x.assignment.id}
                assignment={x.assignment}
                classCode={x.classCode}
                className={x.className}
                submission={x.submission}
                to={`/student/assignments/${x.assignment.id}`}
              />
            ))}
          </div>
        )}
      </section>
    </PageContainer>
  );
}

function greeting() {
  const h = new Date().getHours();
  if (h < 5) return "Late night";
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function CardGridSkeleton() {
  return (
    <div className={layouts.grid}>
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i} padding="lg">
          <Skeleton width={60} height={20} radius="pill" />
          <div style={{ height: 8 }} />
          <Skeleton width="80%" height={20} />
          <div style={{ height: 6 }} />
          <Skeleton width="100%" height={14} />
          <Skeleton width="70%" height={14} />
        </Card>
      ))}
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className={layouts.list}>
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i} padding="md">
          <Skeleton width="40%" height={16} />
          <div style={{ height: 6 }} />
          <Skeleton width="20%" height={12} />
        </Card>
      ))}
    </div>
  );
}
