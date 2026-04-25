import { useRef, useState, type DragEvent, type ChangeEvent } from "react";
import clsx from "clsx";
import { UploadCloud, FileText, X } from "lucide-react";
import styles from "./FileDropzone.module.css";

export interface FileDropzoneProps {
  onFiles: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  hint?: string;
  files?: File[];
  onRemove?: (index: number) => void;
  className?: string;
  disabled?: boolean;
}

export function FileDropzone({
  onFiles,
  accept,
  multiple = false,
  hint = "PDF, DOCX, ZIP up to 25MB",
  files = [],
  onRemove,
  className,
  disabled,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const handle = (list: FileList | null) => {
    if (!list || disabled) return;
    const arr = Array.from(list);
    onFiles(multiple ? arr : arr.slice(0, 1));
  };

  return (
    <div className={clsx(styles.wrap, className)}>
      <div
        className={clsx(styles.zone, over && styles.over, disabled && styles.disabled)}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e: DragEvent) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e: DragEvent) => {
          e.preventDefault();
          setOver(false);
          handle(e.dataTransfer.files);
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
      >
        <UploadCloud size={28} className={styles.cloud} />
        <p className={styles.title}>
          <strong>Drop files here</strong> or click to browse
        </p>
        <p className={styles.hint}>{hint}</p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          className={styles.input}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            handle(e.target.files);
            e.target.value = "";
          }}
          disabled={disabled}
        />
      </div>

      {files.length > 0 && (
        <ul className={styles.list}>
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`} className={styles.item}>
              <FileText size={18} className={styles.fileIcon} />
              <div className={styles.meta}>
                <span className={styles.name}>{f.name}</span>
                <span className={styles.size}>{formatBytes(f.size)}</span>
              </div>
              {onRemove && (
                <button
                  type="button"
                  className={styles.remove}
                  aria-label={`Remove ${f.name}`}
                  onClick={() => onRemove(i)}
                >
                  <X size={14} />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
