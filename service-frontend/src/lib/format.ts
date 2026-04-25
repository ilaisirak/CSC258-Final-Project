// Tiny utility helpers used across pages.

export function formatDate(iso: string, opts?: Intl.DateTimeFormatOptions): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    ...opts,
  });
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function relativeTime(iso: string): string {
  const target = new Date(iso).getTime();
  const now = Date.now();
  const diff = target - now;
  const abs = Math.abs(diff);
  const minutes = Math.round(abs / 60000);
  const hours = Math.round(abs / 3_600_000);
  const dayMs = 86_400_000;
  const days = Math.round(abs / dayMs);

  const fmt = (n: number, unit: string) => `${n} ${unit}${n === 1 ? "" : "s"}`;

  let phrase: string;
  if (minutes < 1) phrase = "moment";
  else if (minutes < 60) phrase = fmt(minutes, "minute");
  else if (hours < 24) phrase = fmt(hours, "hour");
  else if (days < 30) phrase = fmt(days, "day");
  else phrase = fmt(Math.round(days / 30), "month");

  return diff >= 0 ? `in ${phrase}` : `${phrase} ago`;
}

export function dueTone(iso: string): "danger" | "warning" | "neutral" {
  const diff = new Date(iso).getTime() - Date.now();
  const days = diff / 86_400_000;
  if (days < 0) return "danger";
  if (days < 2) return "warning";
  return "neutral";
}

export function gradePercent(score: number, max: number): number {
  if (!max) return 0;
  return Math.round((score / max) * 100);
}

export function gradeLetter(percent: number): string {
  if (percent >= 93) return "A";
  if (percent >= 90) return "A-";
  if (percent >= 87) return "B+";
  if (percent >= 83) return "B";
  if (percent >= 80) return "B-";
  if (percent >= 77) return "C+";
  if (percent >= 73) return "C";
  if (percent >= 70) return "C-";
  if (percent >= 60) return "D";
  return "F";
}
