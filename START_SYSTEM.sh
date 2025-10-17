#!/bin/bash
# CareerPilot System Startup Script

echo "🚀 Starting CareerPilot System..."
echo "================================="

# Go to project root
cd "$(dirname "$0")"

# Start Backend
echo ""
echo "1️⃣ Starting Backend API..."
cd backend
source venv/bin/activate 2>/dev/null || echo "Virtual environment not found, using system Python"
uvicorn app.main:app --reload --port 8001 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend started (PID: $BACKEND_PID) on http://localhost:8001"
cd ..

# Start Frontend
echo ""
echo "2️⃣ Starting Frontend..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend started (PID: $FRONTEND_PID) on http://localhost:3000"
cd ..

# Start Worker
echo ""
echo "3️⃣ Starting Gemini Apply Worker..."
cd backend
python workers/gemini_apply_worker.py --interval 300 > ../logs/worker.log 2>&1 &
WORKER_PID=$!
echo "   ✅ Worker started (PID: $WORKER_PID)"
cd ..

# Save PIDs
mkdir -p logs
echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid
echo "$WORKER_PID" > logs/worker.pid

echo ""
echo "================================="
echo "✅ ALL SYSTEMS RUNNING!"
echo "================================="
echo ""
echo "📋 Services:"
echo "   🌐 Frontend:  http://localhost:3000"
echo "   🔧 Backend:   http://localhost:8001"
echo "   🤖 Worker:    Running (check: http://localhost:8001/worker/health)"
echo ""
echo "📊 Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
echo "   Worker:   tail -f logs/worker.log"
echo ""
echo "🛑 To stop all services: ./STOP_SYSTEM.sh"
echo ""

