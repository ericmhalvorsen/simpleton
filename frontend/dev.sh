#!/bin/bash
# Development startup script for Simpleton Frontend

echo "🚀 Starting Simpleton Frontend..."
echo ""
echo "📦 Installing dependencies..."
bun install

echo ""
echo "🔥 Starting development server with hot reload..."
echo "   Frontend: http://localhost:5173"
echo "   Backend should be running on: http://localhost:8000"
echo ""

bun run dev
