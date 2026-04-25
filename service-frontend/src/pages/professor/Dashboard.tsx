import { useMemo } from "react";
import { Link } from "react-router-dom";
import { BookOpen, ClipboardCheck, Plus, TrendingUp, Users } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Button, Card, EmptyState, Skeleton } from "@/components/ui";
import { ClassCard } from "@/components/domain/ClassCard";
import { StatCard } from "@/components/domain/StatCard";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import { gradePercent } from "@/lib/format";
import layouts from "@/styles/layouts.module.css";

export function ProfessorDashboardPage() {
  const { user } = useAuth();
  const profId = user!.id;

  const classesQ = useQuery(() => api.classes.list({ professorId: profId }), [profId]);

  const classIds = (classesQ.data ?? []).map((c) => c.id);
  // Aggregate assignments + submissions across all professor's classes.
  const aggQ = useQuery(async () => {
    const classes = await api.classes.list({ professorId: profId });
    const all = await Promise.all(
      classes.map(async (c) => {
        const assigns = await api.assignments.listForClass(c.id);
        const subs = await Promise.all(
          assigns.map((a) => api.submissions.listForAssignment(a.id)),
        );
        return { cls: c, assigns, subs: subs.flat() };
      }),
    );
    return all;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profId, classIds.join("|")]);

  const stats = useMemo(() => {
    if (!aggQ.data) return null;
    const allSubs = aggQ.data.flatMap((x) => x.subs);
    const pending = allSubs.filter((s) => !s.grade);
    const graded = allSubs.filter((s) => s.grade);
    const avg =
      graded.length === 0
        ? null
        : Math.round(
            graded.reduce(
              (acc, s) => acc + gradePercent(s.grade!.score, s.grade!.pointsPossible),
              0,
            ) / graded.length,
          );
    return {
      classCount: aggQ.data.length,
      pending: pending.length,
      avg,
      gradedCount: graded.length,
    };
  }, [aggQ.data]);

  const queue = useMemo(() => {
    if (!aggQ.data) return [];
    const items = aggQ.data.flatMap((x) =>
      x.subs
        .filter((s) => !s.grade)
        .map((s) => {
          const a = x.assigns.find((y) => y.id === s.assignmentId)!;
          return { sub: s, assignment: a, cls: x.cls };
        }),
    );
    return items
      .sort((a, b) => new Date(b.sub.submittedAt).getTime() - new Date(a.sub.submittedAt).getTime())
      .slice(0, 5);
  }, [aggQ.data]);

  return (
    <PageContainer>
      <PageHeader
        eyebrow="Overview"
        title={`Welcome, ${user!.name.split(" ")[0]}`}
        description="A snapshot of your classes, the grading queue, and recent performance."
        actions={
          <Link to="/professor/classes/new">
            <Button iconLeft={<Plus size={16} />}>New class</Button>
          </Link>
        }
      />

      <div className={layouts.statGrid}>
        <StatCard
          label="Classes"
          value={stats?.classCount ?? "—"}
          icon={<BookOpen size={18} />}
          tone="accent"
        />
        <StatCard
          label="Awaiting grading"
          value={stats?.pending ?? "—"}
          icon={<ClipboardCheck size={18} />}
          tone={stats && stats.pending > 0 ? "warning" : "neutral"}
        />
        <StatCard
          label="Class average"
          value={stats?.avg === null || stats?.avg === undefined ? "—" : `${stats.avg}%`}
          icon={<TrendingUp size={18} />}
          tone="success"
          hint={stats?.gradedCount ? `Across ${stats.gradedCount} graded` : undefined}
        />
      </div>

      <section className={layouts.section}>
        <div className={layouts.sectionHeading}>
          <h2 className={layouts.sectionTitle}>Needs grading</h2>
          <Link to="/professor/grading" className={layouts.sectionAction}>
            Open queue
          </Link>
        </div>
        {aggQ.loading ? (
          <Card padding="md">
            <Skeleton width="60%" />
          </Card>
        ) : queue.length === 0 ? (
          <EmptyState
            icon={<ClipboardCheck />}
            title="All caught up"
            description="No submissions are waiting for a grade right now."
          />
        ) : (
          <div className={layouts.list}>
            {queue.map(({ sub, assignment, cls }) => (
              <Card key={sub.id} padding="md" interactive>
                <Link
                  to={`/professor/classes/${cls.id}/assignments/${assignment.id}/grade`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    color: "inherit",
                    gap: "var(--space-3)",
                  }}
                >
                  <div>
                    <strong>{sub.studentName}</strong>{" "}
                    <span style={{ color: "var(--c-text-muted)" }}>
                      submitted {assignment.title}
                    </span>
                    <div style={{ fontSize: "var(--fs-xs)", color: "var(--c-text-subtle)" }}>
                      {cls.code} · {cls.name}
                    </div>
                  </div>
                  <Button variant="secondary" size="sm">
                    Grade
                  </Button>
                </Link>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className={layouts.section}>
        <div className={layouts.sectionHeading}>
          <h2 className={layouts.sectionTitle}>Your classes</h2>
          <Link to="/professor/classes" className={layouts.sectionAction}>
            View all
          </Link>
        </div>
        {classesQ.loading ? (
          <Card padding="lg">
            <Skeleton width="40%" />
          </Card>
        ) : (classesQ.data?.length ?? 0) === 0 ? (
          <EmptyState
            icon={<Users />}
            title="No classes yet"
            description="Create your first class to start posting assignments."
            action={
              <Link to="/professor/classes/new">
                <Button iconLeft={<Plus size={16} />}>New class</Button>
              </Link>
            }
          />
        ) : (
          <div className={layouts.grid}>
            {classesQ.data!.map((c) => (
              <ClassCard key={c.id} cls={c} to={`/professor/classes/${c.id}`} />
            ))}
          </div>
        )}
      </section>
    </PageContainer>
  );
}
