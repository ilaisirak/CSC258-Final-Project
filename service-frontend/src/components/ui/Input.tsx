import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";
import clsx from "clsx";
import styles from "./Input.module.css";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, iconLeft, iconRight, className, id, ...rest },
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
        {iconLeft && <span className={clsx(styles.icon, styles.iconLeft)}>{iconLeft}</span>}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedById}
          className={clsx(styles.input, iconLeft && styles.hasLeft, iconRight && styles.hasRight)}
          {...rest}
        />
        {iconRight && <span className={clsx(styles.icon, styles.iconRight)}>{iconRight}</span>}
      </div>
      {(hint || error) && (
        <p id={describedById} className={clsx(styles.help, error && styles.helpError)}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
});
