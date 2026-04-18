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
STORAGE_TYPE=minio

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

GCS_BUCKET=insert-google-bucket-name-here
```

`.env` files are not committed. Each developer creates their own.

---

## Running Locally (Single Service)

1. Clone the repository

2. Create environment file (view above section)

3. Start MinIO (Download: https://dl.min.io/server/minio/release/windows-amd64/minio.exe)

* Navigate to minio.exe

* Run following command (replace D:\ with repository directory)

```bash
minio.exe server D:\
```

4. Build and run a service

```bash
cd service-submission
docker build -t service-submission .
docker run --env-file ../.env -p 8000:8000 service-submission
```

5. Access API

* http://localhost:8000
* http://localhost:8000/docs

---

## Running Locally with Kind

1. Ensure [Kind](https://kind.sigs.k8s.io/) and `kubectl` are installed

2. Create your environment file (see above section)

3. Run the deployment script from the project root:

```bat
local_deploy.bat
```

This will automatically:
- Create the Kind cluster `csc258-finalproject-cluster` (if it doesn't exist)
- Build Docker images for all services
- Load images into the Kind cluster
- Deploy MinIO via `k8/minio/`
- Apply all Kubernetes manifests from `k8/`
- Wait for all service rollouts to complete

4. Access API

* http://localhost:8000
* http://localhost:8000/docs

---

## Cloud Deployment (GCP)

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
* README
* [Contribution]

**Elliot Harrison**

* [Contribution]
* [Contribution]

**Ilai Sirak**

* [Contribution]
* [Contribution]

---
