import { useMemo, useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, ChevronLeft, ChevronRight, FileText } from "lucide-react";
import { PageContainer } from "@/components/layout";
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Skeleton,
  Textarea,
  useToast,
} from "@/components/ui";
import { SubmissionStatusBadge } from "@/components/domain/SubmissionStatusBadge";
import { api } from "@/api/client";
import { useMutation, useQuery } from "@/api/hooks";
import { formatDateTime, gradePercent } from "@/lib/format";
import type { Submission } from "@/api/types";
import styles from "./Grading.module.css";

export function ProfessorGradingPage() {
  const { classId = "", assignmentId = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const assignQ = useQuery(() => api.assignments.get(assignmentId), [assignmentId]);
  const subsQ = useQuery(
    () => api.submissions.listForAssignment(assignmentId),
    [assignmentId],
  );

  const sorted = useMemo<Submission[]>(() => {
    if (!subsQ.data) return [];
    // Ungraded first (newest first), then graded.
    const ungraded = subsQ.data
      .filter((s) => !s.grade)
      .sort((a, b) => new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime());
    const graded = subsQ.data
      .filter((s) => s.grade)
      .sort((a, b) => new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime());
    return [...ungraded, ...graded];
  }, [subsQ.data]);

  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    if (!activeId && sorted.length > 0) setActiveId(sorted[0]!.id);
  }, [sorted, activeId]);

  const active = sorted.find((s) => s.id === activeId) ?? null;
  const idx = active ? sorted.findIndex((s) => s.id === active.id) : -1;

  // Per-submission editor state — keyed by submission id so switching keeps drafts.
  const [drafts, setDrafts] = useState<Record<string, { score: string; feedback: string }>>(
    {},
  );

  useEffect(() => {
    if (!active) return;
    setDrafts((prev) => {
      if (prev[active.id]) return prev;
      return {
        ...prev,
        [active.id]: {
          score: active.grade ? String(active.grade.score) : "",
          feedback: active.grade?.feedback ?? "",
        },
      };
    });
  }, [active]);

  const draft = active ? drafts[active.id] ?? { score: "", feedback: "" } : null;

  const setDraft = (patch: Partial<{ score: string; feedback: string }>) => {
    if (!active) return;
    setDrafts((prev) => ({
      ...prev,
      [active.id]: { ...(prev[active.id] ?? { score: "", feedback: "" }), ...patch },
    }));
  };

  const grade = useMutation(async () => {
    if (!active || !assignQ.data) throw new Error("No active submission");
    const score = Number(draft!.score);
    if (Number.isNaN(score)) throw new Error("Score must be a number");
    if (score < 0 || score > assignQ.data.pointsPossible)
      throw new Error(`Score must be between 0 and ${assignQ.data.pointsPossible}`);
    return api.grading.upsertGrade({
      submissionId: active.id,
      score,
      pointsPossible: assignQ.data.pointsPossible,
      feedback: draft!.feedback || undefined,
    });
  });

  const handleSave = async (advance: boolean) => {
    try {
      await grade.mutate(undefined as never);
      toast.success("Grade saved");
      await subsQ.refetch();
      if (advance) {
        const next = sorted.find((s) => !s.grade && s.id !== active?.id);
        if (next) setActiveId(next.id);
      }
    } catch (err) {
      toast.error(
        "Couldn't save",
        err instanceof Error ? err.message : "Please try again.",
      );
    }
  };

  return (
    <PageContainer>
      <Link to={`/professor/classes/${classId}`} className={styles.back}>
        <ArrowLeft size={14} /> Back to class
      </Link>

      {assignQ.loading ? (
        <Skeleton width="50%" height={28} />
      ) : assignQ.data ? (
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Grading</p>
            <h1 className={styles.title}>{assignQ.data.title}</h1>
            <p className={styles.sub}>
              {assignQ.data.pointsPossible} pts ·{" "}
              {sorted.filter((s) => !s.grade).length} pending ·{" "}
              {sorted.filter((s) => s.grade).length} graded
            </p>
          </div>
          <Button variant="ghost" onClick={() => navigate(`/professor/classes/${classId}`)}>
            Done
          </Button>
        </header>
      ) : null}

      <div className={styles.split}>
        <aside className={styles.list}>
          {subsQ.loading ? (
            <Skeleton width="100%" height={300} radius="lg" />
          ) : sorted.length === 0 ? (
            <EmptyState
              icon={<FileText />}
              title="No submissions yet"
              description="Once students submit, they’ll show up here."
            />
          ) : (
            <ul className={styles.subList}>
              {sorted.map((s) => (
                <li key={s.id}>
                  <button
                    className={
                      s.id === activeId ? `${styles.subItem} ${styles.subActive}` : styles.subItem
                    }
                    onClick={() => setActiveId(s.id)}
                  >
                    <Avatar name={s.studentName} size="sm" />
                    <span className={styles.subMeta}>
                      <span className={styles.subName}>{s.studentName}</span>
                      <span className={styles.subTime}>{formatDateTime(s.submittedAt)}</span>
                    </span>
                    <SubmissionStatusBadge submission={s} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <section className={styles.viewer}>
          {!active ? (
            <Card padding="lg">
              <EmptyState title="Select a submission" description="Pick one from the list to grade." />
            </Card>
          ) : (
            <>
              <Card padding="lg">
                <div className={styles.viewerHeader}>
                  <div className={styles.studentRow}>
                    <Avatar name={active.studentName} />
                    <div>
                      <strong>{active.studentName}</strong>
                      <div className={styles.subTime}>
                        Submitted {formatDateTime(active.submittedAt)}
                      </div>
                    </div>
                  </div>
                  <div className={styles.nav}>
                    <Button
                      variant="ghost"
                      size="sm"
                      iconLeft={<ChevronLeft size={16} />}
                      onClick={() => idx > 0 && setActiveId(sorted[idx - 1]!.id)}
                      disabled={idx <= 0}
                    >
                      Prev
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      iconRight={<ChevronRight size={16} />}
                      onClick={() => idx < sorted.length - 1 && setActiveId(sorted[idx + 1]!.id)}
                      disabled={idx >= sorted.length - 1}
                    >
                      Next
                    </Button>
                  </div>
                </div>

                <h3 className={styles.sectionH}>Files</h3>
                {active.files.length === 0 ? (
                  <p style={{ color: "var(--c-text-muted)", fontSize: "var(--fs-sm)" }}>
                    No files attached.
                  </p>
                ) : (
                  <ul className={styles.files}>
                    {active.files.map((f) => (
                      <li key={f.id} className={styles.fileItem}>
                        <FileText size={16} className={styles.fileIcon} />
                        {f.url ? (
                          <a
                            href={f.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.fileLink}
                          >
                            {f.name}
                          </a>
                        ) : (
                          <span className={styles.fileName}>{f.name}</span>
                        )}
                        <span className={styles.fileSize}>{formatBytes(f.sizeBytes)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>

              <Card padding="lg">
                <h3 className={styles.sectionH}>Grade</h3>
                <div className={styles.gradeRow}>
                  <div className={styles.scoreField}>
                    <Input
                      label="Score"
                      type="number"
                      min={0}
                      max={assignQ.data?.pointsPossible}
                      value={draft?.score ?? ""}
                      onChange={(e) => setDraft({ score: e.target.value })}
                    />
                  </div>
                  <div className={styles.outOf}>
                    / {assignQ.data?.pointsPossible ?? 0}
                  </div>
                  {draft?.score && !Number.isNaN(Number(draft.score)) && assignQ.data ? (
                    <Badge
                      tone={
                        gradePercent(Number(draft.score), assignQ.data.pointsPossible) >= 80
                          ? "success"
                          : gradePercent(Number(draft.score), assignQ.data.pointsPossible) >= 60
                            ? "warning"
                            : "danger"
                      }
                    >
                      {gradePercent(Number(draft.score), assignQ.data.pointsPossible)}%
                    </Badge>
                  ) : null}
                </div>

                <Textarea
                  label="Feedback"
                  rows={6}
                  placeholder="Comments visible to the student…"
                  value={draft?.feedback ?? ""}
                  onChange={(e) => setDraft({ feedback: e.target.value })}
                />

                <div className={styles.actions}>
                  <Button variant="secondary" onClick={() => handleSave(false)} loading={grade.loading}>
                    Save grade
                  </Button>
                  <Button onClick={() => handleSave(true)} loading={grade.loading}>
                    Save & next
                  </Button>
                </div>
              </Card>
            </>
          )}
        </section>
      </div>
    </PageContainer>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
