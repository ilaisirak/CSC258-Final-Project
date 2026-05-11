import { useMemo, useState } from "react";
import { ClipboardList } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Card, EmptyState, Select, Skeleton } from "@/components/ui";
import { AssignmentRow } from "@/components/domain/AssignmentRow";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import layouts from "@/styles/layouts.module.css";

type Filter = "all" | "upcoming" | "submitted" | "graded" | "overdue";

export function StudentAssignmentsPage() {
  const { user } = useAuth();
  const [filter, setFilter] = useState<Filter>("all");

  const { data, loading } = useQuery(
    () => api.assignments.listForStudent(user!.id),
    [user!.id],
  );

  const filtered = useMemo(() => {
    if (!data) return [];
    const sorted = [...data].sort(
      (a, b) =>
        new Date(a.assignment.dueAt).getTime() - new Date(b.assignment.dueAt).getTime(),
    );
    // isOpen and isOverdue are computed by the assignment service so the
    // backend remains the single source of truth for an assignment's state.
    switch (filter) {
      case "upcoming":
        return sorted.filter((x) => x.assignment.isOpen && !x.submission);
      case "submitted":
        return sorted.filter((x) => x.submission && !x.submission.grade);
      case "graded":
        return sorted.filter((x) => x.submission?.grade);
      case "overdue":
        return sorted.filter((x) => x.assignment.isOverdue && !x.submission);
      default:
        return sorted;
    }
  }, [data, filter]);

  return (
    <PageContainer>
      <PageHeader
        eyebrow="Your work"
        title="Assignments"
        description="Across every class — filter to find what you need."
        actions={
          <div style={{ width: 200 }}>
            <Select value={filter} onChange={(e) => setFilter(e.target.value as Filter)}>
              <option value="all">All</option>
              <option value="upcoming">Upcoming</option>
              <option value="submitted">Submitted</option>
              <option value="graded">Graded</option>
              <option value="overdue">Overdue</option>
            </Select>
          </div>
        }
      />

      {loading ? (
        <div className={layouts.list}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} padding="md">
              <Skeleton width="60%" />
            </Card>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<ClipboardList />}
          title="Nothing here"
          description="Try a different filter or check back soon."
        />
      ) : (
        <div className={layouts.list}>
          {filtered.map((x) => (
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
    </PageContainer>
  );
}
