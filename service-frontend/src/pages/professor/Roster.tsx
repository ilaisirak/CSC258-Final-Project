import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Select,
  Skeleton,
} from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import styles from "./Roster.module.css";

export function ProfessorRosterPage() {
  const { user } = useAuth();
  const classesQ = useQuery(
    () => api.classes.list({ professorId: user!.id }),
    [user!.id],
  );

  const [classId, setClassId] = useState<string>("");
  const [filter, setFilter] = useState("");

  // Default to first class once loaded.
  useEffect(() => {
    if (!classId && classesQ.data && classesQ.data.length > 0) {
      setClassId(classesQ.data[0]!.id);
    }
  }, [classId, classesQ.data]);

  const rosterQ = useQuery(
    () => (classId ? api.classes.roster(classId) : Promise.resolve([])),
    [classId],
  );

  const filtered = (rosterQ.data ?? []).filter(
    (s) =>
      !filter ||
      s.name.toLowerCase().includes(filter.toLowerCase()) ||
      s.email.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <PageContainer>
      <PageHeader
        eyebrow="People"
        title="Roster"
        description="Browse students across all of your classes."
      />

      <div className={styles.controls}>
        <div style={{ minWidth: 220 }}>
          <Select value={classId} onChange={(e) => setClassId(e.target.value)}>
            {(classesQ.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </Select>
        </div>
        <div style={{ flex: 1 }}>
          <Input
            placeholder="Filter by name or email…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
        <Button variant="secondary" disabled>
          Export CSV
        </Button>
      </div>

      {classesQ.loading || rosterQ.loading ? (
        <Card padding="lg">
          <Skeleton width="100%" height={120} />
        </Card>
      ) : (classesQ.data?.length ?? 0) === 0 ? (
        <EmptyState
          icon={<Users />}
          title="No classes yet"
          description="Create a class first to see its roster."
        />
      ) : filtered.length === 0 ? (
        <EmptyState title="No students match" description="Try a different filter." />
      ) : (
        <Card padding="none">
          <ul className={styles.list}>
            {filtered.map((s) => (
              <li key={s.id} className={styles.item}>
                <Avatar name={s.name} />
                <div className={styles.meta}>
                  <span className={styles.name}>{s.name}</span>
                  <span className={styles.email}>{s.email}</span>
                </div>
                <Badge tone="neutral" size="sm">
                  Student
                </Badge>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </PageContainer>
  );
}
