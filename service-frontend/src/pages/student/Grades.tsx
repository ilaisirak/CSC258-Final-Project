import { GraduationCap } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Card, EmptyState, Skeleton, Table } from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import { formatDate, gradeLetter, gradePercent } from "@/lib/format";

export function StudentGradesPage() {
  const { user } = useAuth();
  const { data, loading } = useQuery(
    () => api.assignments.listForStudent(user!.id),
    [user!.id],
  );

  const graded = (data ?? []).filter((x) => x.submission?.grade);

  return (
    <PageContainer>
      <PageHeader
        eyebrow="Performance"
        title="Grades"
        description="A complete record of your returned work."
      />

      {loading ? (
        <Card padding="lg">
          <Skeleton width="100%" height={120} />
        </Card>
      ) : graded.length === 0 ? (
        <EmptyState
          icon={<GraduationCap />}
          title="No grades yet"
          description="Once a professor returns work, your grades will land here."
        />
      ) : (
        <Table>
          <Table.Head>
            <tr>
              <Table.HeadCell>Class</Table.HeadCell>
              <Table.HeadCell>Assignment</Table.HeadCell>
              <Table.HeadCell>Returned</Table.HeadCell>
              <Table.HeadCell align="right">Score</Table.HeadCell>
              <Table.HeadCell align="right">Letter</Table.HeadCell>
            </tr>
          </Table.Head>
          <Table.Body>
            {graded.map((x) => {
              const g = x.submission!.grade!;
              const pct = gradePercent(g.score, g.pointsPossible);
              return (
                <Table.Row key={x.assignment.id}>
                  <Table.Cell>
                    <strong>{x.classCode}</strong>{" "}
                    <span style={{ color: "var(--c-text-muted)" }}>{x.className}</span>
                  </Table.Cell>
                  <Table.Cell>{x.assignment.title}</Table.Cell>
                  <Table.Cell>
                    <span style={{ color: "var(--c-text-muted)" }}>{formatDate(g.gradedAt)}</span>
                  </Table.Cell>
                  <Table.Cell align="right">
                    {g.score} / {g.pointsPossible}{" "}
                    <span style={{ color: "var(--c-text-subtle)" }}>({pct}%)</span>
                  </Table.Cell>
                  <Table.Cell align="right">
                    <strong>{gradeLetter(pct)}</strong>
                  </Table.Cell>
                </Table.Row>
              );
            })}
          </Table.Body>
        </Table>
      )}
    </PageContainer>
  );
}
