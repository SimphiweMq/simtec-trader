# 🚀 SIMTEK TRADER - DEPLOYMENT QUICK REFERENCE

## 5-Minute Deployment (Docker)

```bash
# 1. Clone & Setup
git clone https://github.com/SimphiweMq/simtek-trader.git
cd simtek-trader
cp .env.example .env

# 2. Edit Environment
nano .env  # Update with your production settings

# 3. Deploy
./deploy.sh production

# 4. Verify
curl http://localhost:8002/health
curl http://localhost/
```

---

## File Structure Created

```
simtek-trader/
├── Dockerfile.backend              # Backend container
├── Dockerfile.frontend             # Frontend + Nginx
├── docker-compose.yml              # Dev/Test setup
├── docker-compose.production.yml   # Production setup
├── deploy.sh                       # Deployment automation ✅ Executable
├── Makefile                        # Helper commands
│
├── .env                            # Development config
├── .env.example                    # Template
├── .env.production                 # Production template
├── .dockerignore                   # Docker build filter
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions CI/CD
│
├── DEPLOYMENT.md                   # Full deployment guide
├── DEPLOYMENT_CHECKLIST.md        # Pre-flight checks
├── ENV_REFERENCE.md               # Environment variables
├── QUICKSTART_DEPLOY.md           # Platform quick starts
├── PRODUCTION_READY.md            # Summary & architecture
│
├── frontend/
│   ├── nginx.conf                 # Nginx production config
│   ├── .env                       # Frontend dev vars
│   ├── .env.production            # Frontend prod vars
│   └── ...
│
└── src/
    ├── main.py                    # Updated for env vars
    └── ...
```

---

## Deployment Platforms

| Platform | Command | Time | Cost | Complexity |
|----------|---------|------|------|------------|
| **Docker Compose (VPS/EC2)** | `./deploy.sh` | 5 min | $5-20/mo | ⭐ Easy |
| **AWS EC2** | See DEPLOYMENT.md | 10 min | $10-50/mo | ⭐⭐ Medium |
| **Google Cloud Run** | gcloud deploy | 5 min | $0-50/mo | ⭐⭐ Medium |
| **Heroku** | git push | 3 min | $7-50/mo | ⭐ Easy |
| **DigitalOcean** | doctl apps | 5 min | $5-25/mo | ⭐⭐ Medium |
| **Kubernetes** | kubectl apply | 10 min | $10-100/mo | ⭐⭐⭐ Hard |

---

## Key Features

- ✅ Multi-stage Docker builds (small, fast, secure)
- ✅ Auto-restart & health checks
- ✅ Environment-based configuration
- ✅ Nginx with optimization & caching
- ✅ PostgreSQL isolation (not exposed)
- ✅ SSL/HTTPS ready
- ✅ Zero-downtime deployments
- ✅ Monitoring friendly
- ✅ Scaling ready

---

## Before Deploying

### Required
- [ ] Docker & Docker Compose installed (if using Docker)
- [ ] Database ready (PostgreSQL)
- [ ] Domain name (if using HTTPS)
- [ ] SSL certificate (Let's Encrypt or other)

### Configuration (.env)
```ini
# Required
POSTGRES_PASSWORD=secure_password
DATABASE_URL=postgresql://user:password@host/db
VITE_API_URL=https://your-domain.com

# Optional (defaults provided)
ENVIRONMENT=production
BACKEND_PORT=8002
POSTGRES_USER=simtek_user
```

### Checklist
- [ ] All environment variables configured
- [ ] Database credentials secure
- [ ] SSL certificates obtained
- [ ] Firewall rules: Allow 80, 443
- [ ] DNS pointing to server
- [ ] Backups configured
- [ ] Monitoring enabled

---

## Deployment Steps

### Step 1: Prepare Server
```bash
# Ubuntu 22.04 LTS
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose git -y
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Clone & Configure
```bash
git clone https://github.com/SimphiweMq/simtek-trader.git
cd simtek-trader

# Copy and edit environment
cp .env.example .env
nano .env  # Update DATABASE_URL, VITE_API_URL, etc.
```

### Step 3: Deploy
```bash
# Option A: Automated script
./deploy.sh production

# Option B: Manual
docker-compose -f docker-compose.production.yml up -d

# Option C: With logging
docker-compose -f docker-compose.production.yml up -d --remove-orphans
```

### Step 4: Verify
```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f

# Test backend
curl http://localhost:8002/health
curl http://localhost:8002/tickers

# Test frontend
curl http://localhost/

# View specific logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

---

## Common Commands

```bash
# View logs
docker-compose logs -f              # All
docker-compose logs -f backend      # Backend only
docker-compose logs -f frontend     # Frontend only

# Stop/Start
docker-compose down                 # Stop all
docker-compose up -d                # Start all
docker-compose restart              # Restart all

# Debug
docker-compose exec backend sh      # Shell in backend
docker-compose exec postgres psql   # SQL prompt

# Updates
git pull origin main                # Get latest code
docker-compose build                # Rebuild images
docker-compose up -d                # Restart with new images

# Health checks
curl http://localhost:8002/health
curl http://localhost:8002/tickers
curl http://localhost:8002/signal/NPN
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | `sudo lsof -i :8002` then kill process |
| Database won't connect | Check `DATABASE_URL`, verify PostgreSQL running |
| Frontend can't reach API | Check `VITE_API_URL`, verify nginx proxy config |
| Services won't start | Check logs: `docker-compose logs` |
| Out of disk space | `docker system prune -a` |
| Rebuilt images not running | `docker-compose up -d --force-recreate` |

---

## Monitoring & Maintenance

### Daily
- Check service status: `docker-compose ps`
- View error logs: `docker-compose logs`

### Weekly
- Database backups verified
- Disk space monitored
- Security updates applied

### Monthly
- Performance review
- Security audit
- Cost optimization

---

## Rollback

```bash
# Revert to previous version
git log --oneline | head -5      # Find previous commit
git checkout <commit-hash>        # Go back
docker-compose build              # Rebuild
docker-compose up -d              # Restart
```

---

## Support

📖 **Documentation:**
- DEPLOYMENT.md - Full guide
- DEPLOYMENT_CHECKLIST.md - Pre-flight checklist
- ENV_REFERENCE.md - Environment guide
- QUICKSTART_DEPLOY.md - Platform guides

🔗 **Repository:**
https://github.com/SimphiweMq/simtek-trader

---

**Ready to deploy? Start with:** `./deploy.sh production`
