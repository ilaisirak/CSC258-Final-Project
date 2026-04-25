import type { HTMLAttributes, ReactNode } from "react";
import clsx from "clsx";
import styles from "./Badge.module.css";

export type BadgeTone =
  | "neutral"
  | "accent"
  | "success"
  | "warning"
  | "danger"
  | "info";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  size?: "sm" | "md";
  children: ReactNode;
}

export function Badge({ tone = "neutral", size = "md", className, children, ...rest }: BadgeProps) {
  return (
    <span className={clsx(styles.badge, styles[tone], styles[size], className)} {...rest}>
      {children}
    </span>
  );
}
