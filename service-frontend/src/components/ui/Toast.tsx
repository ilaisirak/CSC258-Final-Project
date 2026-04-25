import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import clsx from "clsx";
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from "lucide-react";
import styles from "./Toast.module.css";

type ToastTone = "success" | "danger" | "warning" | "info";

interface ToastItem {
  id: number;
  tone: ToastTone;
  title: string;
  description?: string;
}

interface ToastContextValue {
  show: (t: Omit<ToastItem, "id">) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const idRef = useRef(0);

  const remove = useCallback((id: number) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
  }, []);

  const show = useCallback<ToastContextValue["show"]>(
    (t) => {
      idRef.current += 1;
      const id = idRef.current;
      setItems((prev) => [...prev, { id, ...t }]);
      window.setTimeout(() => remove(id), 4500);
    },
    [remove],
  );

  const value: ToastContextValue = {
    show,
    success: (title, description) => show({ tone: "success", title, description }),
    error: (title, description) => show({ tone: "danger", title, description }),
    info: (title, description) => show({ tone: "info", title, description }),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className={styles.host} role="status" aria-live="polite">
        {items.map((t) => (
          <ToastView key={t.id} item={t} onClose={() => remove(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

const iconFor: Record<ToastTone, ReactNode> = {
  success: <CheckCircle2 size={18} />,
  danger: <XCircle size={18} />,
  warning: <AlertTriangle size={18} />,
  info: <Info size={18} />,
};

function ToastView({ item, onClose }: { item: ToastItem; onClose: () => void }) {
  const [leaving, setLeaving] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setLeaving(true), 4200);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className={clsx(styles.toast, styles[item.tone], leaving && styles.leaving)}>
      <span className={styles.icon}>{iconFor[item.tone]}</span>
      <div className={styles.body}>
        <p className={styles.title}>{item.title}</p>
        {item.description && <p className={styles.desc}>{item.description}</p>}
      </div>
      <button className={styles.close} aria-label="Dismiss" onClick={onClose}>
        <X size={14} />
      </button>
    </div>
  );
}
