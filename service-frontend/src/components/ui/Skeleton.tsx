import clsx from "clsx";
import styles from "./Skeleton.module.css";

export interface SkeletonProps {
  width?: number | string;
  height?: number | string;
  radius?: "sm" | "md" | "lg" | "pill";
  className?: string;
}

export function Skeleton({ width, height = 16, radius = "sm", className }: SkeletonProps) {
  return (
    <span
      className={clsx(styles.s, styles[radius], className)}
      style={{ width, height }}
      aria-hidden
    />
  );
}
