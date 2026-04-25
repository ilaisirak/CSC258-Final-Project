import { Link } from "react-router-dom";
import { Button } from "@/components/ui";
import { useAuth } from "@/app/AuthContext";

export function NotFoundPage() {
  const { user } = useAuth();
  const home = user ? (user.role === "professor" ? "/professor" : "/student") : "/login";
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: "var(--space-4)",
        padding: "var(--space-6)",
        textAlign: "center",
      }}
    >
      <h1 style={{ fontSize: "var(--fs-3xl)" }}>404</h1>
      <p style={{ color: "var(--c-text-muted)" }}>This page doesn’t exist.</p>
      <Link to={home}>
        <Button variant="secondary">Go home</Button>
      </Link>
    </div>
  );
}
