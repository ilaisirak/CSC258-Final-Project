import type { HTMLAttributes, ReactNode } from "react";
import clsx from "clsx";
import styles from "./Table.module.css";

export function Table({
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLTableElement> & { children: ReactNode }) {
  return (
    <div className={styles.scroll}>
      <table className={clsx(styles.table, className)} {...rest}>
        {children}
      </table>
    </div>
  );
}

Table.Head = function THead({ children }: { children: ReactNode }) {
  return <thead className={styles.thead}>{children}</thead>;
};

Table.Body = function TBody({ children }: { children: ReactNode }) {
  return <tbody>{children}</tbody>;
};

Table.Row = function TRow({
  children,
  onClick,
  className,
}: {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <tr
      className={clsx(styles.row, onClick && styles.clickable, className)}
      onClick={onClick}
    >
      {children}
    </tr>
  );
};

Table.Cell = function TCell({
  children,
  align,
  width,
  className,
}: {
  children: ReactNode;
  align?: "left" | "center" | "right";
  width?: number | string;
  className?: string;
}) {
  return (
    <td
      className={clsx(styles.cell, align && styles[`align-${align}`], className)}
      style={{ width }}
    >
      {children}
    </td>
  );
};

Table.HeadCell = function THeadCell({
  children,
  align,
  width,
}: {
  children: ReactNode;
  align?: "left" | "center" | "right";
  width?: number | string;
}) {
  return (
    <th className={clsx(styles.headCell, align && styles[`align-${align}`])} style={{ width }}>
      {children}
    </th>
  );
};
