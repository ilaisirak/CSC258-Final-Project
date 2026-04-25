import clsx from "clsx";
import styles from "./Avatar.module.css";

export interface AvatarProps {
  name: string;
  size?: "sm" | "md" | "lg";
  src?: string;
  className?: string;
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

function colorFor(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  // Stable hue, soft EDU palette
  const hue = h % 360;
  return `hsl(${hue}, 45%, 78%)`;
}

export function Avatar({ name, size = "md", src, className }: AvatarProps) {
  return (
    <span
      className={clsx(styles.avatar, styles[size], className)}
      style={!src ? { background: colorFor(name) } : undefined}
      aria-label={name}
      title={name}
    >
      {src ? <img src={src} alt="" className={styles.img} /> : initials(name) || "?"}
    </span>
  );
}
