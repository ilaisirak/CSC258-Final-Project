import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/api/client";
import type { Role, User } from "@/api/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  role: Role | null;
  signIn: (role: Role, name: string) => Promise<User>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api.users
      .me()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback<AuthContextValue["signIn"]>(async (role, name) => {
    const u = await api.users.signIn(role, name);
    setUser(u);
    return u;
  }, []);

  const signOut = useCallback<AuthContextValue["signOut"]>(async () => {
    await api.users.signOut();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, role: user?.role ?? null, signIn, signOut }),
    [user, loading, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

// Convenience for components that always need a user (rendered inside AppShell).
export function useCurrentUser(): User {
  const { user } = useAuth();
  if (!user) throw new Error("Expected an authenticated user in this tree");
  return user;
}
