# CSC258 Final Project - Student Grading System

## Overview

This project implements a microservices-based student grading system using Docker and Kubernetes. The system supports assignment management, submissions, grading, and user/class management.

Key design principles:

* Microservice architecture
* Database per service
* API Gateway using Kubernetes Ingress
* Environment-based configuration

---

## Architecture

### Services

* User Service
* Assignment Service
* Submission Service
* Grading Service
* Class Service

### Storage

* Relational databases (per service)
* File storage:

  * MinIO (local development)
  * Google Cloud Storage (cloud deployment)

---

## Dependencies

* Python 3.11
* FastAPI
* Docker
* Kubernetes
* Kind (Kubernetes in Docker) — for local deployment only

Python libraries:

* fastapi
* uvicorn
* minio
* google-cloud-storage
* python-multipart

---

## Environment Configuration

Environment variables are used to switch between local and cloud setups.

Example .env:

```bash
# Storage
STORAGE_TYPE=minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
GCS_BUCKET=TBD

# Frontend API mode
VITE_API_MODE=mock

# Per-namespace overrides: mock -> http as each service is confirmed working
VITE_API_USERS=http
VITE_API_CLASSES=http
VITE_API_ASSIGNMENTS=http
VITE_API_SUBMISSIONS=mock
VITE_API_GRADING=http
```

`.env` files are not committed. Each developer creates their own.

---

## Running Locally

### Docker Compose (recommended for development)

Use this for day-to-day development. Starts all services, databases, and MinIO
together without needing a Kubernetes cluster.

1. Clone the repository

2. Create environment file (view above section)

3. Start the full stack

```bash
docker-compose up --build
```

4. To start only a specific service and its dependencies

```bash
docker-compose up --build service-assignment postgres-assignments minio
```

5. Available endpoints once running

| Service            | URL                                                        |
|--------------------|------------------------------------------------------------|
| Frontend           | http://localhost:3000                                      |
| service-assignment | http://localhost:8001/health OR http://localhost:8001/docs |
| service-class      | http://localhost:8002/health OR http://localhost:8002/docs |
| service-grading    | http://localhost:8003/health OR http://localhost:8003/docs |
| service-submission | http://localhost:8004/health OR http://localhost:8004/docs |
| service-user       | http://localhost:8005/health OR http://localhost:8005/docs |
| MinIO Console      | http://localhost:9001                                      |

6. To stop all running containers

```bash
docker-compose down
```

To stop and wipe all local database and storage volumes (clean slate):

```bash
docker-compose down -v
```

---

### kind (Kubernetes in Docker) - Not yet tested

Use this when you want to test your Kubernetes manifests locally before deploying
to GKE. Requires [kind](https://kind.sigs.k8s.io/) and 
[kubectl](https://kubernetes.io/docs/tasks/tools/) to be installed.

1. Create a local cluster

```bash
kind create cluster --name grading-portal
```

2. Load your service images into the cluster (repeat for each service)

```bash
kind load docker-image service-assignment --name grading-portal
kind load docker-image service-class --name grading-portal
kind load docker-image service-grading --name grading-portal
kind load docker-image service-submission --name grading-portal
kind load docker-image service-user --name grading-portal
```

3. Apply your Kubernetes manifests

```bash
kubectl apply -f kubernetes/
```

4. To delete the cluster when done

```bash
kind delete cluster --name grading-portal
```

---

## Cloud Deployment (GCP) - Not yet tested

The system is designed for deployment on Google Cloud Platform.

Required services:

* Kubernetes Engine (GKE)
* Google Cloud Storage

Changes for cloud:

* Set `STORAGE_TYPE=gcs`
* Remove MinIO deployment
* Provide service account credentials

---

## Service Communication

* External requests routed through Ingress
* Internal communication via REST APIs
* Service discovery handled by Kubernetes

---

## Team Information

### Members and Contributions

**Jeremy Auradou**

* Establishing initial code environment (setting up MinIO, kind, FastAPI, file structure, etc.)
* Set up assignment, class, grading, and user services.
* Made README

**Elliott Harrison**

* Quality control, code review

**Ilai Sirak**

* Frontend

---
