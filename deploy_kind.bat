@echo off
setlocal enabledelayedexpansion

:: ──────────────────────────────────────────────
::  CONFIGURATION – change these if needed
:: ──────────────────────────────────────────────
set "K8S_CLUSTER_NAME=csc258-final-project-cluster"
set "FRONTEND_IMAGE=grading-portal/service-frontend:local"

:: ──────────────────────────────────────────────
::  Step 0 – Ensure kind & kubectl are available
:: ──────────────────────────────────────────────
where kind >nul 2>&1
if errorlevel 1 (
    echo ERROR: "kind" not found in PATH.
    echo Please install kind: https://kind.sigs.k8s.io/docs/user/quick-start/
    pause
    exit /b 1
)

where kubectl >nul 2>&1
if errorlevel 1 (
    echo ERROR: "kubectl" not found in PATH.
    echo Please install kubectl: https://kubernetes.io/docs/tasks/tools/
    pause
    exit /b 1
)

:: ──────────────────────────────────────────────
::  Check if kind cluster exists & switch context
:: ──────────────────────────────────────────────
echo Checking kind cluster "%K8S_CLUSTER_NAME%" ...
kind get clusters | findstr /i /c:"%K8S_CLUSTER_NAME%" >nul
if errorlevel 1 (
    echo Cluster not found. Create it with:
    echo   kind create cluster --name %K8S_CLUSTER_NAME%
    pause
    exit /b 1
)

echo Switching kubectl context to kind-%K8S_CLUSTER_NAME% ...
kubectl config use-context kind-%K8S_CLUSTER_NAME%
if errorlevel 1 (
    echo Failed to switch context. Please run manually:
    echo   kubectl config use-context kind-%K8S_CLUSTER_NAME%
    pause
    exit /b 1
)

:: ──────────────────────────────────────────────
::  Step 1 – Build all Docker images
:: ──────────────────────────────────────────────
cd /d %~dp0
echo.
echo ============================================
echo  Building service images ...
echo ============================================

echo [1/6] service-assignment
docker build -t service-assignment:latest .\service-assignment || goto :error

echo [2/6] service-class
docker build -t service-class:latest .\service-class || goto :error

echo [3/6] service-grading
docker build -t service-grading:latest .\service-grading || goto :error

echo [4/6] service-submission
docker build -t service-submission:latest .\service-submission || goto :error

echo [5/6] service-user
docker build -t service-user:latest .\service-user || goto :error

echo [6/6] frontend
docker build -t %FRONTEND_IMAGE% .\service-frontend || goto :error

:: ──────────────────────────────────────────────
::  Step 2 – Load images into kind
:: ──────────────────────────────────────────────
echo.
echo ============================================
echo  Loading images into kind cluster ...
echo ============================================

for %%i in (
    service-assignment:latest
    service-class:latest
    service-grading:latest
    service-submission:latest
    service-user:latest
    %FRONTEND_IMAGE%
) do (
    echo Loading %%i
    kind load docker-image %%i --name %K8S_CLUSTER_NAME% || goto :error
)

:: ──────────────────────────────────────────────
::  Step 3 – Apply Kubernetes manifests
:: ──────────────────────────────────────────────
echo.
echo ============================================
echo  Applying Kubernetes manifests ...
echo ============================================
kubectl apply -f kubernetes\ --recursive || goto :error

:: ──────────────────────────────────────────────
::  Step 4 – Wait for pods (optional)
:: ──────────────────────────────────────────────
echo.
echo Waiting for pods to become ready (timeout 120s) ...
kubectl wait --for=condition=Ready pods --all --timeout=120s || echo Some pods may still be starting...

:: ──────────────────────────────────────────────
::  Success
:: ──────────────────────────────────────────────
echo.
echo ============================================
echo  Deployment complete!
echo ============================================
echo.
set /p START_FORWARD="Start port-forwarding to http://localhost:8080 now? (Y/N): "
if /i "%START_FORWARD%"=="Y" (
    echo.
    echo Port-forwarding... Press Ctrl+C to stop.
    kubectl port-forward svc/service-frontend 8080:80
) else (
    echo.
    echo When ready, run:
    echo   kubectl port-forward svc/service-frontend 8080:80
    echo and open http://localhost:8080.
)
pause
exit /b 0