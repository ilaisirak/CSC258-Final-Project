@echo off
setlocal enabledelayedexpansion

echo =====================================
echo KIND KUBERNETES DEPLOYMENT PIPELINE
echo =====================================

REM =========================
REM CONFIGURATION
REM =========================
set CLUSTER_NAME=csc258-finalproject-cluster

set SERVICES=user-service assignment-service submission-service grading-service class-service

echo.
echo Checking Kubernetes context...
kubectl config current-context

REM =========================
REM CREATE KIND CLUSTER (if needed)
REM =========================
echo.
echo Creating Kind cluster (if not exists)...

kind get clusters | findstr /C:"%CLUSTER_NAME%" >nul
if errorlevel 1 (
    echo Cluster not found. Creating...
    kind create cluster --name %CLUSTER_NAME%
) else (
    echo Cluster already exists. Skipping creation.
)

REM =========================
REM BUILD DOCKER IMAGES
REM =========================
echo.
echo Building Docker images...

for %%S in (%SERVICES%) do (
    echo -------------------------------------
    echo Building %%S...

    docker build -t %%S:latest .\%%S

    if errorlevel 1 (
        echo Failed to build %%S
        exit /b 1
    )
)

REM =========================
REM LOAD IMAGES INTO KIND
REM =========================
echo.
echo Loading images into Kind cluster...

for %%S in (%SERVICES%) do (
    echo Loading %%S into Kind...
    kind load docker-image %%S:latest --name %CLUSTER_NAME%

    if errorlevel 1 (
        echo Failed to load %%S into Kind
        exit /b 1
    )
)

REM =========================
REM DEPLOY MINIO (local only)
REM =========================
echo.
echo Applying MinIO manifests...
kubectl apply -f k8/minio/

if errorlevel 1 (
    echo MinIO deployment failed.
    exit /b 1
)

REM =========================
REM DEPLOY TO KUBERNETES
REM =========================
echo.
echo Applying Kubernetes manifests...

kubectl apply -f k8/

if errorlevel 1 (
    echo Deployment failed.
    exit /b 1
)

REM =========================
REM WAIT FOR ROLLOUTS
REM =========================
echo.
echo Waiting for rollouts to complete...

for %%S in (%SERVICES%) do (
    echo Waiting for %%S...
    kubectl rollout status deployment/%%S --timeout=90s

    if errorlevel 1 (
        echo Rollout timed out or failed for %%S
        exit /b 1
    )
)

echo.
echo =====================================
echo DEPLOYMENT COMPLETE (KIND)
echo =====================================
echo.
echo Useful commands:
echo   kubectl get pods
echo   kubectl get services
echo   kubectl logs -f deployment/submission-service

endlocal
pause
