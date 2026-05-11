import { useMemo } from "react";
import { Link } from "react-router-dom";
import { ClipboardCheck } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Badge, Button, Card, EmptyState, Skeleton } from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import { formatDateTime, relativeTime } from "@/lib/format";
import layouts from "@/styles/layouts.module.css";

export function ProfessorGradingQueuePage() {
  const { user } = useAuth();
  const profId = user!.id;

  const queueQ = useQuery(() => api.grading.gradingQueue(profId), [profId]);

  // The backend already returns oldest-first; reverse here for newest-first display.
  const sorted = useMemo(
    () =>
      (queueQ.data ?? [])
        .slice()
        .sort(
          (a, b) =>
            new Date(b.submission.submittedAt).getTime() -
            new Date(a.submission.submittedAt).getTime(),
        ),
    [queueQ.data],
  );

  return (
    <PageContainer>
      <PageHeader
        eyebrow="Inbox"
        title="Grading queue"
        description="Submissions across every class waiting for a grade."
      />

      {queueQ.loading ? (
        <Card padding="md">
          <Skeleton width="60%" />
        </Card>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={<ClipboardCheck />}
          title="All caught up"
          description="No pending submissions across your classes."
        />
      ) : (
        <div className={layouts.list}>
          {sorted.map((item) => {
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
                    gap: "var(--space-3)",
                    color: "inherit",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                      <Badge tone="accent" size="sm">
                        {cls.code}
                      </Badge>
                      <strong>{assignment.title}</strong>
                    </div>
                    <div style={{ fontSize: "var(--fs-xs)", color: "var(--c-text-muted)" }}>
                      {sub.studentName} ·{" "}
                      <span title={formatDateTime(sub.submittedAt)}>
                        submitted {relativeTime(sub.submittedAt)}
                      </span>
                    </div>
                  </div>
                  <Button variant="secondary" size="sm">
                    Open
                  </Button>
                </Link>
              </Card>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
