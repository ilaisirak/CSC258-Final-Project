import { forwardRef, type InputHTMLAttributes } from "react";
import clsx from "clsx";
import { Check } from "lucide-react";
import styles from "./Checkbox.module.css";

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(function Checkbox(
  { label, className, ...rest },
  ref,
) {
  return (
    <label className={clsx(styles.wrap, className)}>
      <span className={styles.box}>
        <input ref={ref} type="checkbox" className={styles.input} {...rest} />
        <span className={styles.indicator} aria-hidden>
          <Check size={14} strokeWidth={3} />
        </span>
      </span>
      {label && <span className={styles.label}>{label}</span>}
    </label>
  );
});
