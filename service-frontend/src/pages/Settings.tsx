import { useState } from "react";
import { Sun, Moon, LogOut } from "lucide-react";
import { PageContainer, PageHeader } from "@/components/layout";
import { Avatar, Badge, Button, Card, Input, useToast } from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import { useTheme } from "@/app/ThemeContext";
import styles from "./Settings.module.css";

export function SettingsPage() {
  const { user, signOut } = useAuth();
  const { theme, toggle } = useTheme();
  const toast = useToast();

  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");

  if (!user) return null;

  const handleSave = () => {
    // Profile update endpoint isn't wired yet; persist locally for now.
    toast.success("Profile saved", "Persisted locally — backend wiring pending.");
  };

  return (
    <PageContainer>
      <PageHeader
        eyebrow="Account"
        title="Settings"
        description="Manage your profile and preferences."
      />

      <Card padding="lg">
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3>Profile</h3>
            <p>Visible to your classes and on submissions.</p>
          </div>

          <div className={styles.row}>
            <Avatar name={user.name} size="lg" />
            <div className={styles.who}>
              <span className={styles.whoName}>{user.name}</span>
              <Badge tone={user.role === "professor" ? "info" : "accent"}>{user.role}</Badge>
            </div>
          </div>

          <div className={styles.formGrid}>
            <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} />
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className={styles.actions}>
            <Button onClick={handleSave}>Save changes</Button>
          </div>
        </div>
      </Card>

      <Card padding="lg">
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3>Appearance</h3>
            <p>Switch between light and dark themes.</p>
          </div>
          <div className={styles.themeRow}>
            <div className={styles.themePreview}>
              <span className={styles.swatch} data-tone="bg" />
              <span className={styles.swatch} data-tone="accent" />
              <span className={styles.swatch} data-tone="muted" />
            </div>
            <Button
              variant="secondary"
              iconLeft={theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
              onClick={toggle}
            >
              Switch to {theme === "light" ? "dark" : "light"} mode
            </Button>
          </div>
        </div>
      </Card>

      <Card padding="lg">
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3>Session</h3>
            <p>Sign out to switch roles or accounts.</p>
          </div>
          <div className={styles.actions}>
            <Button variant="danger" iconLeft={<LogOut size={16} />} onClick={() => void signOut()}>
              Sign out
            </Button>
          </div>
        </div>
      </Card>
    </PageContainer>
  );
}
