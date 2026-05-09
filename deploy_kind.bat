@echo off
setlocal enabledelayedexpansion

:: ──────────────────────────────────────────────
::  CONFIGURATION – change these if needed
:: ──────────────────────────────────────────────
set "K8S_CLUSTER_NAME=csc258-final-project-cluster"
set "FRONTEND_IMAGE=grading-portal/service-frontend:local"
set RETRY=0
set MAX_RETRIES=10

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
::  Check if kind cluster exists; create if missing
:: ──────────────────────────────────────────────
echo Checking kind cluster "%K8S_CLUSTER_NAME%" ...
kind get clusters | findstr /i /c:"%K8S_CLUSTER_NAME%" >nul
if errorlevel 1 (
    echo Cluster not found. Attempting to create it now...
    kind create cluster --name %K8S_CLUSTER_NAME%
    if errorlevel 1 (
        echo ERROR: Failed to create kind cluster "%K8S_CLUSTER_NAME%".
        echo Please check Docker and try again.
        pause
        exit /b 1
    )
    echo Cluster created successfully.
) else (
    echo Cluster already exists.
)

echo Switching kubectl context to kind-%K8S_CLUSTER_NAME% ...
kubectl config use-context kind-%K8S_CLUSTER_NAME%
if errorlevel 1 (
    echo Failed to switch context. Please run manually:
    echo   kubectl config use-context kind-%K8S_CLUSTER_NAME%
    pause
    exit /b 1
)

echo Metrics Server not found. Installing for kind cluster...
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
if errorlevel 1 (
    echo ERROR: Failed to download Metrics Server manifest.
    pause
    exit /b 1
)

:: Apply the kind-specific TLS patch using a separate JSON file
kubectl patch deployment metrics-server -n kube-system --type=json --patch-file metrics-server-patch.json
if errorlevel 1 (
    echo ERROR: Failed to patch Metrics Server. Please check cluster logs.
    pause
    exit /b 1
)

echo Waiting for Metrics Server to start...
kubectl rollout status deployment metrics-server -n kube-system --timeout=120s
if errorlevel 1 (
    echo ERROR: Metrics Server did not become ready within 120 seconds.
    pause
    exit /b 1
)

echo Metrics Server installed successfully.

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
echo Waiting for all pods to become ready (up to 5 minutes) ...
set RETRY=0
set MAX_RETRIES=10
:wait_loop
    set NOT_READY=
    for /f "tokens=1,2 delims= " %%i in ('kubectl get pods --no-headers 2^>nul ^| findstr /v /c:"1/1" /c:"2/2"') do set NOT_READY=%%i
    if "%NOT_READY%"=="" (
        echo All pods are ready.
        goto wait_done
    )
    set /a RETRY+=1
    if %RETRY% gtr %MAX_RETRIES% (
        echo WARNING: Not all pods became ready after %MAX_RETRIES% retries.
        echo The following pods are not ready:
        kubectl get pods
        echo.
        echo You can continue, or check individual pod logs.
        goto wait_done
    )
    echo Attempt %RETRY%/%MAX_RETRIES% - waiting 30 seconds...
    timeout /t 30 /nobreak >nul
    goto wait_loop
:wait_done

:: ──────────────────────────────────────────────
::  Success
:: ──────────────────────────────────────────────
echo.
echo ============================================
echo  Deployment complete!
echo ============================================
echo.

:: MinIO port‑forward (optional, required for file uploads)
echo "Starting port-forwarding for MinIO (file uploads) in a new window..."
start "MinIO Port-Forward" cmd /c "kubectl port-forward svc/minio 9000:9000" && echo MinIO Console: http://localhost:9001
echo MinIO port-forward launched in a separate window.

:: Frontend port‑forward (main entry point)
echo "Starting port-forwarding to http://localhost:8080 (frontend)..."
echo.
echo Port-forwarding... Press Ctrl+C to stop.
kubectl port-forward svc/service-frontend 8080:80

pause
exit /b 0