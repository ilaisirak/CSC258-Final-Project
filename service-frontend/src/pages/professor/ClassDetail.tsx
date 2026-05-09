import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ClipboardList, Plus, Users } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Skeleton,
  Tabs,
  Textarea,
  type TabItem,
  useToast,
} from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useMutation, useQuery } from "@/api/hooks";
import { dueTone, formatDate, formatDateTime, relativeTime } from "@/lib/format";
import type { AssignmentStatus } from "@/api/types";
import styles from "./ClassDetail.module.css";

const tabs: TabItem[] = [
  { id: "overview", label: "Overview" },
  { id: "assignments", label: "Assignments" },
  { id: "roster", label: "Roster" },
];

export function ProfessorClassDetailPage() {
  const { classId = "" } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const [tab, setTab] = useState("overview");
  const [newOpen, setNewOpen] = useState(false);

  const classQ = useQuery(() => api.classes.get(classId), [classId]);
  const assignsQ = useQuery(() => api.assignments.listForClass(classId), [classId]);
  const rosterQ = useQuery(() => api.classes.roster(classId), [classId]);

  // New assignment form state
  const [aTitle, setATitle] = useState("");
  const [aDesc, setADesc] = useState("");
  const [aDue, setADue] = useState(defaultDueAt());
  const [aPoints, setAPoints] = useState(100);
  const [aStatus, setAStatus] = useState<AssignmentStatus>("open");
  const [aResub, setAResub] = useState(true);

  const createAssign = useMutation(async () =>
    api.assignments.create({
      classId,
      title: aTitle.trim(),
      description: aDesc.trim(),
      dueAt: new Date(aDue).toISOString(),
      pointsPossible: aPoints,
      status: aStatus,
      allowResubmission: aResub,
    }),
  );

  const handleCreateAssign = async () => {
    if (!aTitle.trim()) {
      toast.error("Title required");
      return;
    }
    try {
      await createAssign.mutate(undefined as never);
      toast.success("Assignment created");
      setNewOpen(false);
      setATitle("");
      setADesc("");
      assignsQ.refetch();
      classQ.refetch();
    } catch (err) {
      toast.error("Couldn't create", err instanceof Error ? err.message : undefined);
    }
  };

  // Roster add – updated: resolve email to UUID first
  const [emailInput, setEmailInput] = useState("");

  // This mutation now accepts an email, searches for the user, then enrolls via UUID
  const addStudent = useMutation(async (email: string) => {
    const users = await api.users.search({ email });
    if (users.length === 0) {
      throw new Error("No user found with that email. Create an account first.");
    }
    const student = users[0];
    await api.classes.addStudent(classId, student.id);
    return student;
  });

  const removeStudent = useMutation(async (uid: string) => api.classes.removeStudent(classId, uid));

  const sortedAssigns = useMemo(
    () =>
      (assignsQ.data ?? []).slice().sort(
        (a, b) => new Date(a.dueAt).getTime() - new Date(b.dueAt).getTime(),
      ),
    [assignsQ.data],
  );

  if (!user) return null;

  return (
    <PageContainer>
      <Link to="/professor/classes" className={styles.back}>
        <ArrowLeft size={14} /> All classes
      </Link>

      {classQ.loading ? (
        <Skeleton width="60%" height={32} />
      ) : classQ.data ? (
        <PageHeader
          eyebrow={classQ.data.term.label}
          title={classQ.data.name}
          description={classQ.data.description}
          actions={
            <>
              <Badge tone="accent">{classQ.data.code}</Badge>
              <Button iconLeft={<Plus size={16} />} onClick={() => setNewOpen(true)}>
                New assignment
              </Button>
            </>
          }
        />
      ) : null}

      <Tabs tabs={tabs} value={tab} onChange={setTab} />

      {tab === "overview" && (
        <div className={styles.statRow}>
          <Card padding="lg">
            <p className={styles.statLabel}>Students</p>
            <p className={styles.statValue}>{classQ.data?.studentCount ?? "—"}</p>
          </Card>
          <Card padding="lg">
            <p className={styles.statLabel}>Assignments</p>
            <p className={styles.statValue}>{classQ.data?.assignmentCount ?? "—"}</p>
          </Card>
          <Card padding="lg">
            <p className={styles.statLabel}>Term</p>
            <p className={styles.statValue} style={{ fontSize: "var(--fs-lg)" }}>
              {classQ.data?.term.label ?? "—"}
            </p>
          </Card>
        </div>
      )}

      {tab === "assignments" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          {assignsQ.loading ? (
            <Skeleton width="100%" height={64} radius="lg" />
          ) : sortedAssigns.length === 0 ? (
            <EmptyState
              icon={<ClipboardList />}
              title="No assignments yet"
              description="Create one to make it visible to students."
              action={
                <Button iconLeft={<Plus size={16} />} onClick={() => setNewOpen(true)}>
                  New assignment
                </Button>
              }
            />
          ) : (
            sortedAssigns.map((a) => {
              const tone = dueTone(a.dueAt);
              return (
                <Card key={a.id} padding="md" interactive>
                  <Link
                    to={`/professor/classes/${classId}/assignments/${a.id}/grade`}
                    className={styles.assignRow}
                  >
                    <div>
                      <strong>{a.title}</strong>
                      <div style={{ fontSize: "var(--fs-xs)", color: "var(--c-text-muted)" }}>
                        {a.pointsPossible} pts ·{" "}
                        <span data-tone={tone} className={styles.due}>
                          due {formatDate(a.dueAt)} ({relativeTime(a.dueAt)})
                        </span>
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
                      <Badge
                        tone={
                          a.status === "open" ? "success" : a.status === "draft" ? "neutral" : "danger"
                        }
                      >
                        {a.status}
                      </Badge>
                      <Button variant="secondary" size="sm">
                        Grade
                      </Button>
                    </div>
                  </Link>
                </Card>
              );
            })
          )}
        </div>
      )}

      {tab === "roster" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <Card padding="md">
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!emailInput.trim()) return;
                try {
                  await addStudent.mutate(emailInput.trim());
                  setEmailInput("");
                  rosterQ.refetch();
                  classQ.refetch();
                  toast.success("Student added");
                } catch (err) {
                  toast.error(
                    "Couldn't add",
                    err instanceof Error ? err.message : undefined,
                  );
                }
              }}
              style={{ display: "flex", gap: "var(--space-2)", alignItems: "flex-end" }}
            >
              <div style={{ flex: 1 }}>
                <Input
                  label="Add student by email"
                  placeholder="student@school.edu"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                />
              </div>
              <Button type="submit" loading={addStudent.loading}>
                Add
              </Button>
            </form>
          </Card>

          {rosterQ.loading ? (
            <Skeleton width="100%" height={120} radius="lg" />
          ) : (rosterQ.data?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<Users />}
              title="No students yet"
              description="Add students by email above."
            />
          ) : (
            <Card padding="none">
              <ul className={styles.roster}>
                {rosterQ.data!.map((s) => (
                  <li key={s.id} className={styles.rosterItem}>
                    <Avatar name={s.name} />
                    <div className={styles.rosterMeta}>
                      <span className={styles.rosterName}>{s.name}</span>
                      <span className={styles.rosterEmail}>{s.email}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={async () => {
                        try {
                          await removeStudent.mutate(s.id);
                          rosterQ.refetch();
                          classQ.refetch();
                          toast.success("Removed");
                        } catch (err) {
                          toast.error(
                            "Couldn't remove",
                            err instanceof Error ? err.message : undefined,
                          );
                        }
                      }}
                    >
                      Remove
                    </Button>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {/* ===== CUSTOM MODAL FOR NEW ASSIGNMENT ===== */}
      {newOpen && (
        <>
          {/* Backdrop */}
          <div
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(20, 14, 8, 0.45)",
              zIndex: 1000,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "var(--space-4)",
              animation: "fade var(--dur-base) ease-out",
            }}
            onClick={() => setNewOpen(false)}
          />
          {/* Dialog */}
          <div
            style={{
              position: "fixed",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              width: "100%",
              maxWidth: 560,
              maxHeight: "calc(100vh - 2 * var(--space-8))",
              background: "var(--c-surface)",
              borderRadius: "var(--radius-lg)",
              boxShadow: "var(--shadow-lg)",
              border: "1px solid var(--c-border)",
              zIndex: 1001,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              animation: "pop var(--dur-base) ease-out",
            }}
          >
            <div style={{ padding: "var(--space-5)", borderBottom: "1px solid var(--c-border)" }}>
              <h3 style={{ fontSize: "var(--fs-xl)", marginBottom: "var(--space-1)" }}>
                New assignment
              </h3>
              <p style={{ color: "var(--c-text-muted)", fontSize: "var(--fs-sm)" }}>
                Students in this class will see it once status is open.
              </p>
            </div>
            <div style={{ padding: "var(--space-5)", overflowY: "auto", flex: 1 }}>
              {/* --- Form fields (identical to before, using native inputs) --- */}
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                <div>
                  <label htmlFor="aTitle" style={labelStyle}>Title</label>
                  <input
                    id="aTitle"
                    name="aTitle"
                    type="text"
                    placeholder="Project 1: Kernel Internals"
                    value={aTitle}
                    onChange={(e) => setATitle(e.target.value)}
                    style={inputStyle}
                    autoFocus
                  />
                </div>
                <Textarea
                  label="Description"
                  rows={4}
                  value={aDesc}
                  onChange={(e) => setADesc(e.target.value)}
                />
                <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-3)" }}>
                  <div>
                    <label htmlFor="aDue" style={labelStyle}>Due</label>
                    <input
                      id="aDue"
                      name="aDue"
                      type="datetime-local"
                      value={aDue}
                      onChange={(e) => setADue(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label htmlFor="aPoints" style={labelStyle}>Points</label>
                    <input
                      id="aPoints"
                      name="aPoints"
                      type="number"
                      min={1}
                      value={aPoints}
                      onChange={(e) => setAPoints(Number(e.target.value))}
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-3)" }}>
                  <div>
                    <label htmlFor="aStatus" style={labelStyle}>Status</label>
                    <select
                      id="aStatus"
                      name="aStatus"
                      value={aStatus}
                      onChange={(e) => setAStatus(e.target.value as AssignmentStatus)}
                      style={inputStyle}
                    >
                      <option value="draft">Draft</option>
                      <option value="open">Open</option>
                      <option value="closed">Closed</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="aResub" style={labelStyle}>Resubmissions</label>
                    <select
                      id="aResub"
                      name="aResub"
                      value={aResub ? "yes" : "no"}
                      onChange={(e) => setAResub(e.target.value === "yes")}
                      style={inputStyle}
                    >
                      <option value="yes">Allowed</option>
                      <option value="no">Not allowed</option>
                    </select>
                  </div>
                </div>
                <p style={{ fontSize: "var(--fs-xs)", color: "var(--c-text-subtle)" }}>
                  Created {formatDateTime(new Date().toISOString())}
                </p>
              </div>
            </div>
            <div style={{ padding: "var(--space-4)", borderTop: "1px solid var(--c-border)", display: "flex", justifyContent: "flex-end", gap: "var(--space-2)" }}>
              <Button variant="ghost" onClick={() => setNewOpen(false)}>Cancel</Button>
              <Button onClick={handleCreateAssign} loading={createAssign.loading}>Create</Button>
            </div>
          </div>
        </>
      )}
    </PageContainer>
  );
}

function defaultDueAt() {
  const d = new Date(Date.now() + 7 * 86_400_000);
  d.setHours(23, 59, 0, 0);
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "var(--fs-sm)",
  fontWeight: 500,
  marginBottom: 6,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: "var(--radius-md)",
  border: "1px solid var(--c-border)",
  background: "var(--c-surface)",
  fontSize: "var(--fs-base)",
  boxSizing: "border-box",
};