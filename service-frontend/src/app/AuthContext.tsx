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
  signIn: (email: string, password: string) => Promise<User>;
  signOut: () => Promise<void>;
  register: (input: {
    name: string;
    email: string;
    password: string;
    role: Role;
  }) => Promise<User>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On boot, attempt to hydrate the session. The api.users.me adapter
  // is responsible for inspecting any persisted token and returning the
  // user it represents (or null if the token is missing/expired). We do
  // not need to manage the token directly here.
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

  const register = useCallback(
    async (input: {
      name: string;
      email: string;
      password: string;
      role: Role;
    }) => {
      const session = await api.users.register(input);
      setUser(session.user);
      return session.user;
    },
    [],
  );

  const signIn = useCallback(async (email: string, password: string) => {
    const session = await api.users.signIn(email, password);
    setUser(session.user);
    return session.user;
  }, []);

  const signOut = useCallback(async () => {
    await api.users.signOut();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, role: user?.role ?? null, signIn, signOut, register }),
    [user, loading, signIn, signOut, register],
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
