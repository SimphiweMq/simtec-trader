# Deployment Guide - Simtek Trader

Production deployment guide for the Simtek Trader trading signal engine.

---

## Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose installed
- Git (for cloning the repository)

### Local Production Build & Test

1. **Clone and navigate to project:**
   ```bash
   cd simtek-trader
   ```

2. **Create production environment file:**
   ```bash
   cp .env.example .env.production
   ```
   
   Edit `.env.production` with your production settings:
   ```bash
   # Backend
   BACKEND_PORT=8002
   BACKEND_HOST=0.0.0.0
   ENVIRONMENT=production
   
   # Database (update with actual credentials)
   POSTGRES_USER=simtek_user
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_DB=simtek_trader
   DATABASE_URL=postgresql://simtek_user:your_secure_password@postgres:5432/simtek_trader
   
   # Frontend
   VITE_API_URL=https://your-domain.com
   ```

3. **Build containers:**
   ```bash
   docker-compose build
   ```

4. **Start services:**
   ```bash
   docker-compose up -d
   ```
   
   Services will be available at:
   - **Frontend:** http://localhost (port 80)
   - **Backend API:** http://localhost:8002
   - **Database:** localhost:5432

5. **Check service health:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

6. **Verify backend is running:**
   ```bash
   curl http://localhost:8002/health
   ```

---

## Production Deployment (Cloud)

### AWS EC2 Deployment

1. **Launch Ubuntu 22.04 LTS instance**
   - Instance type: t3.medium (or larger)
   - Security group: Allow ports 80, 443, 8002, 5432

2. **SSH into instance and install Docker:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   sudo apt-get install -y docker.io docker-compose git
   sudo usermod -aG docker $USER
   ```

3. **Clone repository:**
   ```bash
   git clone https://github.com/SimphiweMq/simtek-trader.git
   cd simtek-trader
   ```

4. **Setup SSL with Let's Encrypt (recommended):**
   ```bash
   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot certonly --standalone -d your-domain.com
   ```

5. **Update nginx config** for SSL (update `frontend/nginx.conf`):
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
       # ... rest of config
   }
   ```

6. **Start services:**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

### Google Cloud Run (Serverless)

For each service (backend & frontend), create separate Cloud Run services:

**Backend:**
```bash
cd simtek-trader
gcloud run deploy simtek-backend \
  --source . \
  --dockerfile Dockerfile.backend \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars "ENVIRONMENT=production,BACKEND_PORT=8080"
```

**Frontend:**
```bash
gcloud run deploy simtek-frontend \
  --source . \
  --dockerfile Dockerfile.frontend \
  --memory 512Mi \
  --set-env-vars "VITE_API_URL=https://simtek-backend-url"
```

---

## Database Migrations

Run database migrations before first deployment:

```bash
# Inside backend container
docker-compose exec backend python -m alembic upgrade head
```

---

## Monitoring

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health checks
```bash
# Backend health
curl http://localhost:8002/health

# Frontend
curl http://localhost/
```

---

## Scaling

For high traffic, scale using:

```bash
# Docker Compose - increase replicas
docker-compose up -d --scale backend=3
```

Or deploy with **Kubernetes** for advanced orchestration.

---

## Security Checklist

- [ ] Update PostgreSQL password in `.env`
- [ ] Use SSL/TLS certificates (Let's Encrypt or CloudFlare)
- [ ] Enable CORS restrictions in backend
- [ ] Keep Docker images updated
- [ ] Use secrets manager for sensitive data (AWS Secrets, etc.)
- [ ] Enable database backups
- [ ] Set up monitoring & alerting
- [ ] Implement rate limiting
- [ ] Use CDN for static assets

---

## Troubleshooting

### Backend won't start
```bash
docker-compose logs backend
# Check DATABASE_URL is correct
```

### Frontend can't reach backend
```bash
# Verify VITE_API_URL is set correctly in container
docker-compose logs frontend
# Check nginx config routes API requests correctly
```

### Database connection error
```bash
# Verify database is healthy
docker-compose ps postgres
docker-compose exec postgres pg_isready
```

---

## Rollback

To rollback to previous version:

```bash
docker-compose down
git checkout previous-commit-hash
docker-compose build
docker-compose up -d
```

---

## Support

For issues or questions, contact: support@simteknologies.com
