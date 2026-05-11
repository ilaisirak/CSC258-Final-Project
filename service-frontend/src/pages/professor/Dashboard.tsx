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
import layouts from "@/styles/layouts.module.css";

export function ProfessorDashboardPage() {
  const { user } = useAuth();
  const profId = user!.id;

  const classesQ = useQuery(() => api.classes.list({ professorId: profId }), [profId]);
  const statsQ = useQuery(() => api.grading.professorStats(profId), [profId]);
  const queueQ = useQuery(() => api.grading.gradingQueue(profId, 5), [profId]);

  const stats = statsQ.data;
  const queue = useMemo(() => queueQ.data ?? [], [queueQ.data]);

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
          value={stats?.pendingCount ?? "—"}
          icon={<ClipboardCheck size={18} />}
          tone={stats && stats.pendingCount > 0 ? "warning" : "neutral"}
        />
        <StatCard
          label="Class average"
          value={
            stats?.avgGrade === null || stats?.avgGrade === undefined
              ? "—"
              : `${Math.round(stats.avgGrade)}%`
          }
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
        {queueQ.loading ? (
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
            {queue.map((item) => {
              const sub = item.submission;
              const assignment = item.assignment;
              const cls = item.class;
              return (
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
              );
            })}
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
