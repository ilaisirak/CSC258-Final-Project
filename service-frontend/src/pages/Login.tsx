import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { GraduationCap, BookOpen } from "lucide-react";
import clsx from "clsx";
import { Button, Input } from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import type { Role } from "@/api/types";
import styles from "./Login.module.css";

export function LoginPage() {
  const { signIn, register } = useAuth();  
  const navigate = useNavigate();
  const [role, setRole] = useState<Role>("student");
  const [name, setName] = useState("");
  const [email, setEmail] = useState(""); 
  const [isCreating, setIsCreating] = useState(false); 
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter your name");
      return;
    }
    if (isCreating && !email.trim()) {
      setError("Please enter your email");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      let u;
      if (isCreating) {
        u = await register(name, email, role);
      } else {
        u = await signIn(role, name);
      }
      navigate(u.role === "professor" ? "/professor" : "/student", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : (isCreating ? "Registration failed" : "Sign-in failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.decor} aria-hidden />
      <div className={styles.card}>
        <div className={styles.brand}>
          <div className={styles.brandMark}>
            <svg viewBox="0 0 32 32" width="28" height="28">
              <rect width="32" height="32" rx="8" fill="currentColor" />
              <path
                d="M9 11h14M9 16h14M9 21h9"
                stroke="#fff"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <h1 className={styles.brandTitle}>Grading Portal</h1>
            <p className={styles.brandSub}>
              {isCreating ? "Create your account" : "Sign in to continue"}
            </p>
          </div>
        </div>

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <fieldset className={styles.roleGroup}>
            <legend className={styles.legend}>I am a…</legend>
            <div className={styles.roleGrid}>
              <RoleCard
                active={role === "student"}
                onClick={() => setRole("student")}
                icon={<GraduationCap size={22} />}
                title="Student"
                description="View classes, submit assignments, track grades."
              />
              <RoleCard
                active={role === "professor"}
                onClick={() => setRole("professor")}
                icon={<BookOpen size={22} />}
                title="Professor"
                description="Manage classes, assignments, and grading."
              />
            </div>
          </fieldset>

          <Input
            label="Your name"
            placeholder={role === "student" ? "Alex Chen" : "Dr. Mira Patel"}
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={error && !isCreating ? error : undefined}
            autoFocus
          />

          {/* Show email field only during account creation */}
          {isCreating && (
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={error && isCreating ? error : undefined}
            />
          )}

          <Button type="submit" size="lg" fullWidth loading={submitting}>
            {isCreating ? "Create Account" : "Continue"}
          </Button>

          <p className={styles.footnote}>
            {isCreating ? (
              <>
                Already have an account?{" "}
                <button
                  type="button"
                  className={styles.footnoteBtn}
                  onClick={() => {
                    setIsCreating(false);
                    setError(null);
                  }}
                >
                  Sign in
                </button>
              </>
            ) : (
              <>
                Don't have an account?{" "}
                <button
                  type="button"
                  className={styles.footnoteBtn}
                  onClick={() => {
                    setIsCreating(true);
                    setError(null);
                  }}
                >
                  Create one
                </button>
              </>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}

// RoleCard component remains unchanged
function RoleCard({
  active,
  onClick,
  icon,
  title,
  description,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(styles.role, active && styles.roleActive)}
      aria-pressed={active}
    >
      <span className={styles.roleIcon}>{icon}</span>
      <span className={styles.roleText}>
        <span className={styles.roleTitle}>{title}</span>
        <span className={styles.roleDesc}>{description}</span>
      </span>
    </button>
  );
}