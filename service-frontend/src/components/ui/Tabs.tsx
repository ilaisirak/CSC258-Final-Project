import type { ReactNode } from "react";
import clsx from "clsx";
import styles from "./Tabs.module.css";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
}

export interface TabsProps {
  tabs: TabItem[];
  value: string;
  onChange: (id: string) => void;
  className?: string;
  rightSlot?: ReactNode;
}

export function Tabs({ tabs, value, onChange, className, rightSlot }: TabsProps) {
  return (
    <div className={clsx(styles.wrap, className)} role="tablist">
      <div className={styles.list}>
        {tabs.map((t) => {
          const active = t.id === value;
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={active}
              tabIndex={active ? 0 : -1}
              className={clsx(styles.tab, active && styles.active)}
              onClick={() => onChange(t.id)}
            >
              <span>{t.label}</span>
              {typeof t.count === "number" && <span className={styles.count}>{t.count}</span>}
            </button>
          );
        })}
      </div>
      {rightSlot && <div className={styles.right}>{rightSlot}</div>}
    </div>
  );
}
