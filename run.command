#!/bin/bash

# Di chuyển thư mục làm việc hiện tại về vị trí của file run.command này
cd "$(dirname "$0")"

echo "🔍 Kiểm tra và dọn dẹp các tiến trình cũ..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo "🚀 Khởi động Backend (cổng 8000)..."
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
fi
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

echo "🚀 Khởi động Frontend React (cổng 5173)..."
cd ../frontend
npm run dev &

# Tự động mở trình duyệt sau 3 giây
(sleep 3 && open http://localhost:5173) &

wait
