import clsx from "clsx";
import styles from "./ProgressBar.module.css";

export interface ProgressBarProps {
  value: number; // 0-100
  tone?: "accent" | "success" | "warning" | "danger";
  size?: "sm" | "md";
  label?: string;
  className?: string;
}

export function ProgressBar({
  value,
  tone = "accent",
  size = "md",
  label,
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className={clsx(styles.wrap, className)}>
      {label && (
        <div className={styles.row}>
          <span className={styles.label}>{label}</span>
          <span className={styles.value}>{Math.round(clamped)}%</span>
        </div>
      )}
      <div
        className={clsx(styles.track, styles[size])}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className={clsx(styles.fill, styles[tone])} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
