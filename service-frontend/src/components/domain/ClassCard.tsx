import { Link } from "react-router-dom";
import { Calendar, Users, BookOpen } from "lucide-react";
import { Badge, Card } from "@/components/ui";
import type { Class } from "@/api/types";
import styles from "./ClassCard.module.css";

export interface ClassCardProps {
  cls: Class;
  to: string;
  showCounts?: boolean;
}

export function ClassCard({ cls, to, showCounts = true }: ClassCardProps) {
  return (
    <Card as="article" padding="lg" interactive className={styles.card}>
      <Link to={to} className={styles.link} aria-label={`Open ${cls.name}`}>
        <div className={styles.header}>
          <div className={styles.codeStripe} />
          <Badge tone="accent" size="sm">
            {cls.code}
          </Badge>
          <span className={styles.term}>{cls.term.label}</span>
        </div>
        <h3 className={styles.title}>{cls.name}</h3>
        {cls.description && <p className={styles.desc}>{cls.description}</p>}
        <div className={styles.footer}>
          <span className={styles.meta}>
            <Calendar size={14} /> {cls.term.label}
          </span>
          {showCounts && (
            <>
              <span className={styles.meta}>
                <Users size={14} /> {cls.studentCount}
              </span>
              <span className={styles.meta}>
                <BookOpen size={14} /> {cls.assignmentCount}
              </span>
            </>
          )}
        </div>
      </Link>
    </Card>
  );
}
