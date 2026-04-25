import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Button, Card, Input, Textarea, useToast } from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import { api } from "@/api/client";
import { useMutation } from "@/api/hooks";

export function ProfessorClassNewPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [termLabel, setTermLabel] = useState(currentTermLabel());
  const [description, setDescription] = useState("");

  const create = useMutation(async () => {
    const today = new Date();
    const startsOn = today.toISOString().slice(0, 10);
    const endsOn = new Date(today.getTime() + 120 * 86_400_000).toISOString().slice(0, 10);
    return api.classes.create({
      code: code.trim(),
      name: name.trim(),
      description: description.trim() || undefined,
      professorId: user!.id,
      professorName: user!.name,
      term: { label: termLabel.trim(), startsOn, endsOn },
    });
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !name.trim()) {
      toast.error("Missing info", "Code and name are required.");
      return;
    }
    try {
      const cls = await create.mutate(undefined as never);
      toast.success("Class created", `${cls.code} is ready for assignments.`);
      navigate(`/professor/classes/${cls.id}`, { replace: true });
    } catch (err) {
      toast.error(
        "Couldn't create",
        err instanceof Error ? err.message : "Please try again.",
      );
    }
  };

  return (
    <PageContainer>
      <Link
        to="/professor/classes"
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

      <PageHeader
        eyebrow="New"
        title="Create a class"
        description="Set up a course shell — you can add assignments and students afterwards."
      />

      <Card padding="lg">
        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 2fr",
              gap: "var(--space-4)",
            }}
          >
            <Input
              label="Code"
              placeholder="CSC258"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            <Input
              label="Name"
              placeholder="Software Engineering"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <Input
            label="Term"
            placeholder="Spring 2026"
            value={termLabel}
            onChange={(e) => setTermLabel(e.target.value)}
          />
          <Textarea
            label="Description"
            placeholder="Brief overview shown to students."
            rows={5}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <div style={{ display: "flex", gap: "var(--space-2)", justifyContent: "flex-end" }}>
            <Link to="/professor/classes">
              <Button variant="ghost" type="button">
                Cancel
              </Button>
            </Link>
            <Button type="submit" loading={create.loading}>
              Create class
            </Button>
          </div>
        </form>
      </Card>
    </PageContainer>
  );
}

function currentTermLabel() {
  const d = new Date();
  const m = d.getMonth();
  const term = m < 5 ? "Spring" : m < 8 ? "Summer" : "Fall";
  return `${term} ${d.getFullYear()}`;
}
