import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Calendar, FileText } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  FileDropzone,
  Skeleton,
  useToast,
} from "@/components/ui";
import { SubmissionStatusBadge } from "@/components/domain/SubmissionStatusBadge";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useMutation, useQuery } from "@/api/hooks";
import { dueTone, formatDate, formatDateTime, gradePercent, relativeTime } from "@/lib/format";
import styles from "./AssignmentDetail.module.css";

export function StudentAssignmentDetailPage() {
  const { assignmentId = "" } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const [files, setFiles] = useState<File[]>([]);

  const assignQ = useQuery(() => api.assignments.get(assignmentId), [assignmentId]);
  const subsQ = useQuery(
    () => api.submissions.listForStudent(user!.id),
    [user!.id, assignmentId],
  );

  const mySubs = useMemo(
    () => (subsQ.data ?? []).filter((s) => s.assignmentId === assignmentId),
    [subsQ.data, assignmentId],
  );
  const latest = mySubs[mySubs.length - 1];

  const submit = useMutation(async () => {
    if (files.length === 0) throw new Error("Please attach at least one file.");
    const sub = await api.submissions.submit({
      assignmentId,
      studentId: user!.id,
      files,
    });
    return sub;
  });

  const handleSubmit = async () => {
    try {
      await submit.mutate(undefined as never);
      toast.success("Submitted", "Your professor will be notified.");
      setFiles([]);
      subsQ.refetch();
    } catch (err) {
      toast.error(
        "Couldn't submit",
        err instanceof Error ? err.message : "Please try again.",
      );
    }
  };

  if (assignQ.loading) {
    return (
      <PageContainer>
        <Skeleton width="50%" height={32} />
        <Skeleton width="100%" height={200} radius="lg" />
      </PageContainer>
    );
  }

  if (!assignQ.data) {
    return (
      <PageContainer>
        <EmptyState title="Assignment not found" description="It may have been removed." />
      </PageContainer>
    );
  }

  const a = assignQ.data;
  const tone = dueTone(a.dueAt);
  const isClosed = a.status === "closed";
  const canSubmit =
    !isClosed && (!latest || (a.allowResubmission && !latest.grade));

  return (
    <PageContainer>
      <Link to="/student/assignments" className={styles.back}>
        <ArrowLeft size={14} /> All assignments
      </Link>

      <PageHeader
        eyebrow="Assignment"
        title={a.title}
        actions={<SubmissionStatusBadge submission={latest} />}
      />

      <div className={styles.metaRow}>
        <span className={styles.metaItem} data-tone={tone}>
          <Calendar size={14} />
          Due {formatDate(a.dueAt)} <span className={styles.rel}>({relativeTime(a.dueAt)})</span>
        </span>
        <Badge tone="neutral">{a.pointsPossible} points</Badge>
        {isClosed && <Badge tone="danger">Closed</Badge>}
      </div>

      <div className={styles.grid}>
        <div className={styles.colMain}>
          <Card padding="lg">
            <h3 className={styles.h}>Description</h3>
            <p className={styles.body}>{a.description}</p>
          </Card>

          <Card padding="lg">
            <h3 className={styles.h}>Submit your work</h3>
            {!canSubmit ? (
              <p className={styles.body} style={{ color: "var(--c-text-muted)" }}>
                {isClosed
                  ? "This assignment is closed."
                  : latest?.grade
                    ? "Your work has been graded — see feedback on the right."
                    : "You've already submitted; resubmissions aren't allowed for this assignment."}
              </p>
            ) : (
              <>
                <FileDropzone
                  files={files}
                  onFiles={(f) => setFiles((prev) => [...prev, ...f])}
                  onRemove={(i) => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
                  multiple
                />
                <div className={styles.submitRow}>
                  <Button
                    onClick={handleSubmit}
                    loading={submit.loading}
                    disabled={files.length === 0}
                  >
                    {latest ? "Resubmit" : "Submit"}
                  </Button>
                  {submit.error && <span className={styles.error}>{submit.error.message}</span>}
                </div>
              </>
            )}
          </Card>

          {mySubs.length > 0 && (
            <Card padding="lg">
              <h3 className={styles.h}>Submission history</h3>
              <ul className={styles.history}>
                {mySubs
                  .slice()
                  .reverse()
                  .map((s) => (
                    <li key={s.id} className={styles.historyItem}>
                      <FileText size={16} className={styles.fileIcon} />
                      <div className={styles.histMeta}>
                        <span className={styles.histTime}>{formatDateTime(s.submittedAt)}</span>
                        <span className={styles.histFiles}>
                          {s.files.map((f) => f.name).join(", ")}
                        </span>
                      </div>
                      <SubmissionStatusBadge submission={s} />
                    </li>
                  ))}
              </ul>
            </Card>
          )}
        </div>

        <aside className={styles.colSide}>
          {latest?.grade ? (
            <Card padding="lg">
              <h3 className={styles.h}>Grade & feedback</h3>
              <div className={styles.score}>
                <span className={styles.scoreNum}>
                  {latest.grade.score}
                  <span className={styles.scoreOf}>/{latest.grade.pointsPossible}</span>
                </span>
                <Badge
                  tone={
                    gradePercent(latest.grade.score, latest.grade.pointsPossible) >= 80
                      ? "success"
                      : gradePercent(latest.grade.score, latest.grade.pointsPossible) >= 60
                        ? "warning"
                        : "danger"
                  }
                >
                  {gradePercent(latest.grade.score, latest.grade.pointsPossible)}%
                </Badge>
              </div>
              {latest.grade.feedback && (
                <p className={styles.feedback}>{latest.grade.feedback}</p>
              )}
              <p className={styles.gradedAt}>Returned {formatDateTime(latest.grade.gradedAt)}</p>
            </Card>
          ) : (
            <Card padding="lg">
              <h3 className={styles.h}>Grade & feedback</h3>
              <p className={styles.body} style={{ color: "var(--c-text-muted)" }}>
                Your grade will appear here once your professor returns this assignment.
              </p>
            </Card>
          )}
        </aside>
      </div>
    </PageContainer>
  );
}
