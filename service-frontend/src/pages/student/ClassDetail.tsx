import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, ClipboardList, GraduationCap } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Badge, Card, EmptyState, Skeleton, Tabs, type TabItem } from "@/components/ui";
import { AssignmentRow } from "@/components/domain/AssignmentRow";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import type { Submission } from "@/api/types";
import { formatDate, gradePercent, gradeLetter } from "@/lib/format";
import layouts from "@/styles/layouts.module.css";

const tabs: TabItem[] = [
  { id: "assignments", label: "Assignments" },
  { id: "grades", label: "Grades" },
  { id: "syllabus", label: "Syllabus" },
];

export function StudentClassDetailPage() {
  const { classId = "" } = useParams();
  const { user } = useAuth();
  const [tab, setTab] = useState("assignments");

  const classQ = useQuery(() => api.classes.get(classId), [classId]);
  const assignsQ = useQuery(() => api.assignments.listForClass(classId), [classId]);
  const subsQ = useQuery(() => api.submissions.listForStudent(user!.id), [user!.id]);

  const subByAssignment = useMemo(() => {
    const map = new Map<string, Submission>();
    (subsQ.data ?? []).forEach((s) => map.set(s.assignmentId, s));
    return map;
  }, [subsQ.data]);

  const graded = useMemo(
    () =>
      (assignsQ.data ?? [])
        .map((a) => ({ assignment: a, submission: subByAssignment.get(a.id) }))
        .filter((x) => x.submission?.grade),
    [assignsQ.data, subByAssignment],
  );

  return (
    <PageContainer>
      <Link
        to="/student/classes"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          fontSize: "var(--fs-sm)",
          color: "var(--c-text-muted)",
        }}
      >
        <ArrowLeft size={14} /> All classes
      </Link>

      {classQ.loading ? (
        <Skeleton width="60%" height={32} />
      ) : classQ.data ? (
        <PageHeader
          eyebrow={classQ.data.term.label}
          title={classQ.data.name}
          description={classQ.data.description}
          actions={<Badge tone="accent">{classQ.data.code}</Badge>}
        />
      ) : null}

      <Tabs tabs={tabs} value={tab} onChange={setTab} />

      {tab === "assignments" && (
        <div className={layouts.list}>
          {assignsQ.loading ? (
            <Skeleton height={64} radius="lg" />
          ) : (assignsQ.data?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<ClipboardList />}
              title="No assignments yet"
              description="Your professor hasn't posted anything for this class."
            />
          ) : (
            assignsQ.data!.map((a) => (
              <AssignmentRow
                key={a.id}
                assignment={a}
                submission={subByAssignment.get(a.id)}
                to={`/student/assignments/${a.id}`}
              />
            ))
          )}
        </div>
      )}

      {tab === "grades" && (
        <Card padding="none">
          {graded.length === 0 ? (
            <div style={{ padding: "var(--space-6)" }}>
              <EmptyState
                icon={<GraduationCap />}
                title="No grades yet"
                description="Once your professor returns work, your grades will appear here."
              />
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--fs-sm)" }}>
              <thead style={{ background: "var(--c-surface-2)" }}>
                <tr>
                  <th style={cellH}>Assignment</th>
                  <th style={cellH}>Returned</th>
                  <th style={{ ...cellH, textAlign: "right" }}>Score</th>
                  <th style={{ ...cellH, textAlign: "right" }}>Letter</th>
                </tr>
              </thead>
              <tbody>
                {graded.map(({ assignment, submission }) => {
                  const g = submission!.grade!;
                  const pct = gradePercent(g.score, g.pointsPossible);
                  return (
                    <tr key={assignment.id} style={{ borderTop: "1px solid var(--c-border)" }}>
                      <td style={cell}>{assignment.title}</td>
                      <td style={{ ...cell, color: "var(--c-text-muted)" }}>
                        {formatDate(g.gradedAt)}
                      </td>
                      <td style={{ ...cell, textAlign: "right" }}>
                        {g.score} / {g.pointsPossible}{" "}
                        <span style={{ color: "var(--c-text-subtle)" }}>({pct}%)</span>
                      </td>
                      <td style={{ ...cell, textAlign: "right", fontWeight: 600 }}>
                        {gradeLetter(pct)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {tab === "syllabus" && (
        <Card padding="lg">
          <h3 style={{ marginBottom: "var(--space-3)" }}>About this class</h3>
          <p style={{ color: "var(--c-text-muted)" }}>
            {classQ.data?.description ??
              "Your professor hasn't published a syllabus yet for this class."}
          </p>
        </Card>
      )}
    </PageContainer>
  );
}

const cellH: React.CSSProperties = {
  textAlign: "left",
  padding: "var(--space-3) var(--space-4)",
  fontWeight: 600,
  fontSize: "var(--fs-xs)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "var(--c-text-muted)",
};

const cell: React.CSSProperties = { padding: "var(--space-3) var(--space-4)" };
