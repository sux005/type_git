#!/bin/bash

# Deployment script for DataHacks backend to EC2
# Usage: ./deploy.sh [ec2-user@ec2-ip] [path-to-backend]

EC2_HOST="${1:-ubuntu@3.15.176.0}"
BACKEND_PATH="${2:-/home/ubuntu/backend}"
KEY_FILE="${3:-}"  # Optional: path to SSH key

echo "🚀 Deploying backend to EC2..."
echo "EC2 Host: $EC2_HOST"
echo "Backend Path: $BACKEND_PATH"

# Build SSH command
if [ -n "$KEY_FILE" ]; then
  SSH_CMD="ssh -i $KEY_FILE"
else
  SSH_CMD="ssh"
fi

# Step 1: Pull latest code
echo ""
echo "📥 Pulling latest code from main branch..."
$SSH_CMD $EC2_HOST "cd $BACKEND_PATH && git pull origin main"

if [ $? -ne 0 ]; then
  echo "❌ Failed to pull code. Check SSH access and repository."
  exit 1
fi

# Step 2: Kill existing uvicorn process
echo ""
echo "🛑 Stopping existing uvicorn server..."
$SSH_CMD $EC2_HOST "pkill -f 'uvicorn' || echo 'No existing process found'"

# Wait a moment for process to terminate
sleep 2

# Step 3: Install/update dependencies
echo ""
echo "📦 Installing dependencies..."
$SSH_CMD $EC2_HOST "cd $BACKEND_PATH && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

if [ $? -ne 0 ]; then
  echo "❌ Failed to install dependencies."
  exit 1
fi

# Step 4: Start new server in background
echo ""
echo "🟢 Starting FastAPI server..."
$SSH_CMD $EC2_HOST "cd $BACKEND_PATH && nohup ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &"

# Brief pause to ensure server starts
sleep 3

# Step 5: Test the endpoint
echo ""
echo "🧪 Testing API endpoint..."
RESPONSE=$(curl -s -X POST http://3.15.176.0:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test",
    "value": 42.0,
    "alert_level": "normal"
  }')

if echo "$RESPONSE" | grep -q "ok\|status"; then
  echo "✅ API is responding!"
  echo "Response: $RESPONSE"
else
  echo "⚠️  API responded but check if it's working correctly"
  echo "Response: $RESPONSE"
fi

# Step 6: Show server logs
echo ""
echo "📋 Recent server logs:"
$SSH_CMD $EC2_HOST "tail -20 $BACKEND_PATH/server.log"

echo ""
echo "✨ Deployment complete!"
echo ""
echo "💡 To monitor the server:"
echo "   ssh $EC2_HOST"
echo "   tail -f $BACKEND_PATH/server.log"
