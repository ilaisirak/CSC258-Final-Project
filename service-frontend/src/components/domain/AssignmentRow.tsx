import { Link } from "react-router-dom";
import { Calendar } from "lucide-react";
import { Badge, Card } from "@/components/ui";
import { SubmissionStatusBadge } from "./SubmissionStatusBadge";
import { dueTone, formatDate, relativeTime } from "@/lib/format";
import type { Assignment, Submission } from "@/api/types";
import styles from "./AssignmentRow.module.css";

export interface AssignmentRowProps {
  assignment: Assignment;
  classCode?: string;
  className?: string; // class name (course)
  submission?: Submission;
  to: string;
}

export function AssignmentRow({
  assignment,
  classCode,
  className: courseName,
  submission,
  to,
}: AssignmentRowProps) {
  const tone = dueTone(assignment.dueAt);
  return (
    <Card padding="md" interactive className={styles.card}>
      <Link to={to} className={styles.link} aria-label={`Open ${assignment.title}`}>
        <div className={styles.left}>
          <div className={styles.titleRow}>
            {classCode && (
              <Badge tone="accent" size="sm">
                {classCode}
              </Badge>
            )}
            <span className={styles.title}>{assignment.title}</span>
          </div>
          {courseName && <span className={styles.course}>{courseName}</span>}
        </div>
        <div className={styles.right}>
          <span className={styles.due} data-tone={tone}>
            <Calendar size={14} />
            <span>
              {formatDate(assignment.dueAt)} <span className={styles.rel}>({relativeTime(assignment.dueAt)})</span>
            </span>
          </span>
          <SubmissionStatusBadge submission={submission} />
        </div>
      </Link>
    </Card>
  );
}
