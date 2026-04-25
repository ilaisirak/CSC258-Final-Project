# service-frontend

React + TypeScript + Vite SPA for the Grading Portal. Renders student and
professor experiences over a typed `ApiClient` — defaults to an in-memory mock
so the UI runs without any backend, and can be swapped to real services
namespace-by-namespace as they come online.

## Stack

- Vite 5 + React 18 + TypeScript (strict)
- React Router 6
- CSS Modules + design-token CSS variables (light/dark)
- `clsx`, `lucide-react` (no UI framework)

## Quick start

```bash
cd service-frontend
npm install
npm run dev          # http://localhost:5173 — uses mock API
```

Other scripts:

| Script             | What it does                              |
| ------------------ | ----------------------------------------- |
| `npm run dev`      | Vite dev server with `/api` proxy         |
| `npm run build`    | `tsc -b && vite build` → `dist/`          |
| `npm run preview`  | Serve the production build locally        |
| `npm run typecheck`| `tsc -b --noEmit`                         |
| `npm run lint`     | ESLint over `src/`                        |
| `npm run format`   | Prettier write                            |

The dev server signs you in by picking a role and a name — no password.
A demo professor and a few students are seeded.

## Project layout

```
src/
  api/
    types.ts                # domain types (User, Class, Assignment, …)
    fixtures.ts             # seed data for the mock adapter
    adapters/
      interfaces.ts         # ApiClient contract
      mock.ts               # in-memory + localStorage adapter (default)
      http.ts               # fetch-based adapter for real services
    client.ts               # picks adapter per namespace via env vars
    hooks.ts                # tiny useQuery / useMutation
  app/
    AuthContext.tsx         # session, sign-in/out
    ThemeContext.tsx        # light/dark, persisted
    guards.tsx              # RequireAuth, RequireRole, RoleHome
    router.tsx              # routes
  components/
    ui/                     # primitives (Button, Card, Modal, Toast, …)
    layout/                 # Sidebar, Topbar, AppShell, PageHeader
    domain/                 # ClassCard, AssignmentRow, StatCard, …
  pages/
    Login, NotFound, Settings
    student/                # Dashboard, Classes, ClassDetail, Assignments,
                            # AssignmentDetail, Grades
    professor/              # Dashboard, Classes, ClassNew, ClassDetail,
                            # GradingQueue, Grading, Roster
  styles/
    tokens.css              # design tokens (single source of truth)
    global.css              # reset + base
    layouts.module.css      # shared grid/list utilities
  lib/format.ts             # date/grade helpers
```

## API mode — mock vs real

The frontend talks to its backend through `ApiClient`, split into namespaces:
`users`, `classes`, `assignments`, `submissions`, `grading`. Each namespace
can be flipped to the real HTTP adapter independently while others remain
mocked — useful while the backend services come online one by one.

Configure via `.env.local` (Vite picks up `VITE_*`):

```bash
# Default for everything: "mock" or "http"
VITE_API_MODE=mock

# Optional per-namespace overrides
VITE_API_USERS=mock
VITE_API_CLASSES=mock
VITE_API_ASSIGNMENTS=mock
VITE_API_SUBMISSIONS=http   # e.g. flip submissions to real backend
VITE_API_GRADING=mock

# Base URL prefix forwarded by the dev proxy (vite.config.ts)
VITE_API_BASE=/api
```

In dev, `vite.config.ts` proxies `/api/*` to `http://localhost:8000` (matches
the existing `kubernetes/ingress.yaml`), stripping the `/api` prefix.

The mock adapter persists the active session to `localStorage` under
`gradingPortal.session`. To inspect or reset its in-memory store, open the
console: `window.__gpStore`.

## Auth

Demo-only role picker: choose "student" or "professor" and any name. The
selection is stored locally and the app routes you to `/student` or
`/professor`. Wire `VITE_API_USERS=http` and implement the `users` adapter on
the backend to take over.

## Theming

Tokens live in `src/styles/tokens.css`. The active theme is set on
`<html data-theme="light|dark">`; `ThemeContext` persists the choice to
`localStorage` and respects `prefers-color-scheme` on first load. Add a new
token by extending both `[data-theme="light"]` and `[data-theme="dark"]`
blocks.

Palette — warm "Friendly EDU" (terracotta accent on beige), with a matched
dark theme.

## Adding a screen

1. Create `src/pages/<role>/<Name>.tsx` (and a `.module.css` if needed).
2. Add a route in `src/app/router.tsx`.
3. Use `PageContainer` + `PageHeader` from `@/components/layout` for shell.
4. Fetch data with `useQuery(() => api.<ns>.<method>(args), [deps])`.
5. Use primitives from `@/components/ui` and domain components from
   `@/components/domain`. Avoid raw colors — pull from
   `var(--c-…)` tokens.

## Build & deploy

```bash
docker build -t grading-portal/frontend:local service-frontend
```

Multi-stage `Dockerfile` builds with Node 20 and serves the static `dist/`
through `nginx:alpine` with SPA fallback (`nginx.conf`). A placeholder
`kubernetes/services/frontend.yaml` is included; it isn't yet wired into
`local_deploy.bat` because the backend ingress contract is still firming up.
Apply it manually once you're ready:

```bash
kubectl apply -f kubernetes/services/frontend.yaml
```

The container listens on port 80; route the cluster ingress to the
`frontend` Service.
