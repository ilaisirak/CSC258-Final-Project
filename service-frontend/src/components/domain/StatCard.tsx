import type { ReactNode } from "react";
import clsx from "clsx";
import { Card } from "@/components/ui";
import styles from "./StatCard.module.css";

export interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  icon?: ReactNode;
  tone?: "neutral" | "accent" | "success" | "warning" | "danger";
  className?: string;
}

export function StatCard({ label, value, hint, icon, tone = "neutral", className }: StatCardProps) {
  return (
    <Card padding="md" className={clsx(styles.card, styles[tone], className)}>
      <div className={styles.row}>
        <span className={styles.label}>{label}</span>
        {icon && <span className={styles.icon}>{icon}</span>}
      </div>
      <div className={styles.value}>{value}</div>
      {hint && <div className={styles.hint}>{hint}</div>}
    </Card>
  );
}
