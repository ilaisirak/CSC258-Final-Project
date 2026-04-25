import { useState } from "react";
import { Menu, Sun, Moon, LogOut } from "lucide-react";
import { Avatar, Badge, IconButton } from "@/components/ui";
import { useAuth } from "@/app/AuthContext";
import { useTheme } from "@/app/ThemeContext";
import styles from "./Topbar.module.css";

interface TopbarProps {
  onToggleSidebar: () => void;
}

export function Topbar({ onToggleSidebar }: TopbarProps) {
  const { user, signOut } = useAuth();
  const { theme, toggle } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className={styles.bar}>
      <div className={styles.left}>
        <button
          type="button"
          className={styles.menuBtn}
          onClick={onToggleSidebar}
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>
      </div>

      <div className={styles.right}>
        <IconButton label={`Switch to ${theme === "light" ? "dark" : "light"} mode`} onClick={toggle}>
          {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
        </IconButton>

        {user && (
          <div className={styles.userWrap}>
            <button
              type="button"
              className={styles.user}
              onClick={() => setMenuOpen((s) => !s)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              <Avatar name={user.name} size="sm" />
              <span className={styles.userMeta}>
                <span className={styles.userName}>{user.name}</span>
                <Badge tone={user.role === "professor" ? "info" : "accent"} size="sm">
                  {user.role}
                </Badge>
              </span>
            </button>
            {menuOpen && (
              <div className={styles.menu} role="menu" onMouseLeave={() => setMenuOpen(false)}>
                <button
                  type="button"
                  className={styles.menuItem}
                  onClick={() => {
                    setMenuOpen(false);
                    void signOut();
                  }}
                  role="menuitem"
                >
                  <LogOut size={16} />
                  Sign out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
