import { forwardRef, useId, type SelectHTMLAttributes, type ReactNode } from "react";
import clsx from "clsx";
import styles from "./Select.module.css";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, hint, error, className, id, children, ...rest },
  ref,
) {
  const reactId = useId();
  const inputId = id ?? reactId;
  const describedById = hint || error ? `${inputId}-desc` : undefined;

  return (
    <div className={clsx(styles.field, className)}>
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
        </label>
      )}
      <div className={clsx(styles.wrap, error && styles.error)}>
        <select
          ref={ref}
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedById}
          className={styles.select}
          {...rest}
        >
          {children}
        </select>
        <span className={styles.chevron} aria-hidden>
          ▾
        </span>
      </div>
      {(hint || error) && (
        <p id={describedById} className={clsx(styles.help, error && styles.helpError)}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
});
