import { Badge, type BadgeTone } from "@/components/ui";
import type { Submission } from "@/api/types";

export interface SubmissionStatusBadgeProps {
  submission?: Submission;
  /** When true, "Not started" is shown instead of nothing for missing submissions. */
  showNotStarted?: boolean;
}

export function SubmissionStatusBadge({
  submission,
  showNotStarted = true,
}: SubmissionStatusBadgeProps) {
  if (!submission) {
    if (!showNotStarted) return null;
    return <Badge tone="neutral">Not started</Badge>;
  }
  if (submission.grade) {
    const pct = Math.round((submission.grade.score / submission.grade.pointsPossible) * 100);
    const tone: BadgeTone = pct >= 80 ? "success" : pct >= 60 ? "warning" : "danger";
    return (
      <Badge tone={tone}>
        Graded · {submission.grade.score}/{submission.grade.pointsPossible}
      </Badge>
    );
  }
  return <Badge tone="info">Submitted</Badge>;
}
