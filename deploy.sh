#!/bin/bash

# Simtek Trader - Production Deployment Script
# Usage: ./deploy.sh <environment>

set -e

ENVIRONMENT=${1:-production}
DOCKER_COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "production" ]; then
    DOCKER_COMPOSE_FILE="docker-compose.production.yml"
fi

echo "=========================================="
echo "Simtek Trader - $ENVIRONMENT Deployment"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and update with your settings"
    exit 1
fi

# Load environment variables
source .env

echo "✅ Environment variables loaded"
echo ""

# Build images
echo "🔨 Building Docker images..."
docker-compose -f "$DOCKER_COMPOSE_FILE" build

echo "✅ Images built successfully"
echo ""

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down 2>/dev/null || true

echo "✅ Services stopped"
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

echo "✅ Services started"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Production URLs:"
    echo "  Frontend: https://your-domain.com"
    echo "  Backend API: https://your-domain.com/api"
else
    echo "Development URLs:"
    echo "  Frontend: http://localhost"
    echo "  Backend API: http://localhost:8002"
    echo "  API Documentation: http://localhost:8002/docs"
fi

echo ""
echo "View logs with: docker-compose logs -f"
