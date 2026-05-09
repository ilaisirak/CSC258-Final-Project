# Grading Portal — CSC258 Final Project

A microservices-based student grading system with Docker Compose (development) and Kubernetes (production) deployment.

---

## For the Professor — What This System Does

This application lets professors and students interact with a simple grading portal.

**Professors** can create classes, add assignments, and set due dates. They can view student rosters and add students by email (no pre-registration required — the system resolves email to an account), grade submitted work, leave feedback, and see submitted files directly in the browser through presigned storage links.

**Students** can sign up with just a name, email, and role — no password required. They can enroll in classes, submit assignments (with file uploads), and view grades and feedback from a dashboard that groups all assignments by class.

Both roles use a single-page React frontend that communicates with a RESTful API. The entire system is self-contained — run it with one command on a single machine, or scale it to many replicas with Kubernetes.

---

## Architecture Highlights

- **Domain-aligned microservices** — each service owns its own PostgreSQL database:
  - `service-user` — user accounts and search
  - `service-class` — classes, rosters, enrollments
  - `service-assignment` — assignments
  - `service-submission` — file uploads (stored in MinIO)
  - `service-grading` — grades and feedback
  - `service-frontend` — React/TypeScript app served by Nginx
- **Per-service database with persistent storage** via Kubernetes StatefulSets and PVCs
- **Connection pooling** via PgBouncer sidecars to keep database connections optimal when autoscaling
- **Horizontal Pod Autoscaler (HPA)** on every backend service — automatically scales pods based on CPU load (70% target)
- **Presigned file storage** — MinIO generates short-lived URLs so the browser can directly download submitted files
- **Email-resolved roster** — professors add students by email; the user service resolves it to a UUID before enrolling

---

## Quick Start — Docker Compose (Local Development)

### Prerequisites

- Docker and Docker Compose v2
- No extra setup — the Compose file starts all services, databases, and MinIO automatically

### Steps

1. Clone the repository.
2. Create a `.env` file in the project root (see example below).
3. Start everything:

```bash
docker-compose up --build
```

4. Access the frontend at http://localhost:3000.

### Example `.env`

```env
STORAGE_TYPE=minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### Useful Commands

| Action | Command |
|---|---|
| Stop all containers | `docker-compose down` |
| Wipe all data (volumes) | `docker-compose down -v` |
| Start only one service | `docker-compose up --build service-assignment postgres-assignments minio` |

### Services and Ports

| Component | URL |
|---|---|
| Frontend | http://localhost:3000 |
| service-user | http://localhost:8005/health (docs at `/docs`) |
| service-class | http://localhost:8002/health |
| service-assignment | http://localhost:8001/health |
| service-submission | http://localhost:8004/health |
| service-grading | http://localhost:8003/health |
| MinIO Console | http://localhost:9001 |

---

## Production-Style Kubernetes Deployment (kind)

We use [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker) to run a full cluster locally. A single batch file automates everything.

### Prerequisites

- Docker Desktop
- `kind` and `kubectl` (install via Chocolatey or direct download)
- (Optional) `hey` for load testing

### One-Command Deployment

```batch
deploy_kind.bat
```

This script:

1. Checks for `kind`/`kubectl` and creates the kind cluster if missing
2. Installs the Metrics Server (required for HPA)
3. Builds all Docker images
4. Loads them into the kind cluster
5. Applies all Kubernetes manifests (databases, services, MinIO, Ingress, HPAs)
6. Waits for all pods to be ready
7. Asks if you want to port-forward the frontend (and optionally MinIO for file access)

After it finishes, you will have a fully working, autoscaling microservices environment.

### Manual Steps (Optional)

Create a cluster:

```bash
kind create cluster --name csc258-final-project-cluster
```

Then build, load, and deploy as described in the batch file.

Port-forward the frontend:

```bash
kubectl port-forward svc/service-frontend 8080:80
```

### MinIO & File Uploads

File submissions are stored in MinIO. To let the browser download files (e.g. on the grading page), you need to port-forward MinIO as well:

```bash
kubectl port-forward svc/minio 9000:9000
```

The batch script offers to open a separate terminal for this automatically.

### Scaling Demonstration

### Stil need to figure this step out

Watch the replicas increase:

```bash
kubectl get hpa -w
```

After the load stops, the HPA will scale back down automatically.

### Clean-Up

```bash
kind delete cluster --name csc258-final-project-cluster
```

---

## Key Changes Since Initial Version

- **Kubernetes deployment** with persistent databases (PostgreSQL StatefulSets), PgBouncer sidecar pooling, and Horizontal Pod Autoscaling
- **Roster additions by email** — frontend resolves email to UUID via `/users/search`, then enrolls via UUID
- **File download fix** — grading page now renders presigned URLs so professors can open submitted files directly
- **Deployment batch file** fully automates cluster creation, image building, manifest application, and optional port-forward
- **Service-specific ConfigMaps** for Nginx (frontend proxy) and PgBouncer (connection pooling)

---

## Project Structure

```
.
├── kubernetes/               # All K8s manifests
│   ├── databases/            # StatefulSets, Services, Secrets for each DB
│   ├── minio/                # MinIO deployment & PVC
│   ├── services/             # Deployments & Services for all microservices + frontend
│   └── ingress.yaml
├── service-assignment/       # FastAPI microservice (similar for user, class, submission, grading)
├── service-frontend/         # React app with Nginx config
├── docker-compose.yaml       # Local development stack
├── deploy_kind.bat           # One-command Kubernetes deployment
└── README.md
```

---

## Team

**Jeremy Auradou**
- Microservice design and backend implementation (all services, database schemas, MinIO integration)
- Kubernetes architecture — StatefulSets, HPA, PgBouncer sidecars, Metrics Server, deployment script
- Frontend-backend integration, API adapters, snake/camel case conversion
- User registration, email-resolved roster, file download fix
- Documentation and README

**Elliott Harrison**
- Quality assurance, code review, testing

**Ilai Sirak**
- Frontend development (React, routing, components, styling)