import type { ReactNode } from "react";
import clsx from "clsx";
import styles from "./EmptyState.module.css";

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={clsx(styles.wrap, className)}>
      {icon && <div className={styles.icon}>{icon}</div>}
      <h4 className={styles.title}>{title}</h4>
      {description && <p className={styles.desc}>{description}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
