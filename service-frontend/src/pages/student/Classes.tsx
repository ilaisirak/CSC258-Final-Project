import { BookOpen } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Card, EmptyState, Skeleton } from "@/components/ui";
import { ClassCard } from "@/components/domain/ClassCard";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useQuery } from "@/api/hooks";
import layouts from "@/styles/layouts.module.css";

export function StudentClassesPage() {
  const { user } = useAuth();
  const { data, loading } = useQuery(
    () => api.classes.list({ studentId: user!.id }),
    [user!.id],
  );

  return (
    <PageContainer>
      <PageHeader
        eyebrow="Your enrollment"
        title="Classes"
        description="Every course you're currently enrolled in."
      />

      {loading ? (
        <div className={layouts.grid}>
          {Array.from({ length: 4 }).map((_, i) => (
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
          description="Once you’re enrolled in a class, it’ll appear here."
        />
      ) : (
        <div className={layouts.grid}>
          {data!.map((c) => (
            <ClassCard key={c.id} cls={c} to={`/student/classes/${c.id}`} />
          ))}
        </div>
      )}
    </PageContainer>
  );
}
