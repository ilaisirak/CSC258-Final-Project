import { forwardRef, useId, type TextareaHTMLAttributes } from "react";
import clsx from "clsx";
import styles from "./Textarea.module.css";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, hint, error, className, id, rows = 4, ...rest },
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
      <textarea
        ref={ref}
        id={inputId}
        rows={rows}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedById}
        className={clsx(styles.input, error && styles.error)}
        {...rest}
      />
      {(hint || error) && (
        <p id={describedById} className={clsx(styles.help, error && styles.helpError)}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
});
