#!/bin/bash
# CareerPilot System Shutdown Script

echo "🛑 Stopping CareerPilot System..."
echo "================================="

cd "$(dirname "$0")"

# Stop Backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    echo "Stopping Backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null && echo "   ✅ Backend stopped" || echo "   ⚠️  Backend not running"
    rm logs/backend.pid
fi

# Stop Frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    echo "Stopping Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null && echo "   ✅ Frontend stopped" || echo "   ⚠️  Frontend not running"
    rm logs/frontend.pid
fi

# Stop Worker
if [ -f logs/worker.pid ]; then
    WORKER_PID=$(cat logs/worker.pid)
    echo "Stopping Worker (PID: $WORKER_PID)..."
    kill $WORKER_PID 2>/dev/null && echo "   ✅ Worker stopped" || echo "   ⚠️  Worker not running"
    rm logs/worker.pid
fi

# Also kill any remaining processes by name
echo ""
echo "Cleaning up any remaining processes..."
pkill -f "uvicorn backend.app.main:app" && echo "   ✅ Killed remaining backend processes"
pkill -f "next dev" && echo "   ✅ Killed remaining frontend processes"
pkill -f "gemini_apply_worker" && echo "   ✅ Killed remaining worker processes"

echo ""
echo "================================="
echo "✅ ALL SYSTEMS STOPPED"
echo "================================="
echo ""

