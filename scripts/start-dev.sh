#!/bin/bash
# Start development servers
echo "Starting LED AI Copilot..."

# Start backend
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
