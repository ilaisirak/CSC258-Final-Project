import { Link } from "react-router-dom";
import { BookOpen, Plus } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Button, Card, EmptyState, Skeleton } from "@/components/ui";
import { ClassCard } from "@/components/domain/ClassCard";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import layouts from "@/styles/layouts.module.css";

export function ProfessorClassesPage() {
  const { user } = useAuth();
  const { data, loading } = useQuery(
    () => api.classes.list({ professorId: user!.id }),
    [user!.id],
  );

  return (
    <PageContainer>
      <PageHeader
        eyebrow="Teaching"
        title="Classes"
        description="Manage rosters, assignments, and grading for every class you teach."
        actions={
          <Link to="/professor/classes/new">
            <Button iconLeft={<Plus size={16} />}>New class</Button>
          </Link>
        }
      />

      {loading ? (
        <div className={layouts.grid}>
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} padding="lg">
              <Skeleton width={60} height={20} radius="pill" />
              <div style={{ height: 8 }} />
              <Skeleton width="80%" height={20} />
              <div style={{ height: 6 }} />
              <Skeleton width="100%" height={14} />
            </Card>
          ))}
        </div>
      ) : (data?.length ?? 0) === 0 ? (
        <EmptyState
          icon={<BookOpen />}
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
          {data!.map((c) => (
            <ClassCard key={c.id} cls={c} to={`/professor/classes/${c.id}`} />
          ))}
        </div>
      )}
    </PageContainer>
  );
}
