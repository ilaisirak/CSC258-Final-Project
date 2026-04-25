import { NavLink } from "react-router-dom";
import clsx from "clsx";
import {
  LayoutDashboard,
  BookOpen,
  ClipboardList,
  GraduationCap,
  Users,
  Settings,
} from "lucide-react";
import type { Role } from "@/api/types";
import styles from "./Sidebar.module.css";

interface SidebarProps {
  role: Role;
  open: boolean;
  onClose: () => void;
}

const studentLinks = [
  { to: "/student", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/student/classes", label: "Classes", icon: BookOpen },
  { to: "/student/assignments", label: "Assignments", icon: ClipboardList },
  { to: "/student/grades", label: "Grades", icon: GraduationCap },
];

const profLinks = [
  { to: "/professor", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/professor/classes", label: "Classes", icon: BookOpen },
  { to: "/professor/grading", label: "Grading queue", icon: ClipboardList },
  { to: "/professor/roster", label: "Roster", icon: Users },
];

export function Sidebar({ role, open, onClose }: SidebarProps) {
  const links = role === "student" ? studentLinks : profLinks;

  return (
    <>
      {open && <div className={styles.scrim} onClick={onClose} aria-hidden />}
      <aside className={clsx(styles.sidebar, open && styles.open)}>
        <div className={styles.brand}>
          <div className={styles.brandMark} aria-hidden>
            <svg viewBox="0 0 32 32" width="22" height="22">
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
            <div className={styles.brandName}>Grading Portal</div>
            <div className={styles.brandRole}>{role === "student" ? "Student" : "Professor"}</div>
          </div>
        </div>

        <nav className={styles.nav} aria-label="Main">
          <ul>
            {links.map(({ to, label, icon: Icon, end }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  onClick={onClose}
                  className={({ isActive }) => clsx(styles.link, isActive && styles.active)}
                >
                  <Icon size={18} className={styles.linkIcon} />
                  <span>{label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className={styles.footer}>
          <NavLink
            to="/settings"
            onClick={onClose}
            className={({ isActive }) => clsx(styles.link, isActive && styles.active)}
          >
            <Settings size={18} className={styles.linkIcon} />
            <span>Settings</span>
          </NavLink>
        </div>
      </aside>
    </>
  );
}
