@echo off
echo Starting port-forwards for all backend services...
echo Each service will open in its own window.
echo Close the individual windows to stop the forwards.
echo.

start "service-assignment :8001" cmd /c "kubectl port-forward svc/service-assignment 8001:80"
start "service-class      :8002" cmd /c "kubectl port-forward svc/service-class 8002:80"
start "service-grade-records :8003" cmd /c "kubectl port-forward svc/service-grade-records 8003:80"
start "service-submission :8004" cmd /c "kubectl port-forward svc/service-submission 8004:80"
start "service-user       :8005" cmd /c "kubectl port-forward svc/service-user 8005:80"

echo.
echo All port-forwards launched.
echo.
echo Swagger UIs:
echo   Assignment : http://localhost:8001/docs
echo   Class      : http://localhost:8002/docs
echo   Grading    : http://localhost:8003/docs
echo   Submission : http://localhost:8004/docs
echo   User       : http://localhost:8005/docs
echo.

echo.
pause