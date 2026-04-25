import { forwardRef, type HTMLAttributes, type ReactNode } from "react";
import clsx from "clsx";
import styles from "./Card.module.css";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  as?: "div" | "section" | "article";
  padding?: "none" | "sm" | "md" | "lg";
  interactive?: boolean;
  children: ReactNode;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { as: _Tag = "div", padding = "md", interactive, className, children, ...rest },
  ref,
) {
  const Tag = _Tag as "div";
  return (
    <Tag
      ref={ref}
      className={clsx(
        styles.card,
        styles[`p-${padding}`],
        interactive && styles.interactive,
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
});
