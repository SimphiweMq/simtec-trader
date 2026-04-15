# Production Deployment Checklist

Complete this checklist before deploying to production.

## Pre-Deployment

- [ ] All tests pass locally
- [ ] Code review completed and approved
- [ ] Database migrations have been tested
- [ ] Environment variables are configured
- [ ] SSL certificates are obtained (Let's Encrypt or other)
- [ ] Domain is configured and DNS is pointing correctly
- [ ] Backups are scheduled and tested
- [ ] Monitoring is configured (logs, metrics, alerts)

## Infrastructure Setup

- [ ] Server/VPS provisioned (Ubuntu 22.04 LTS recommended)
- [ ] Docker and Docker Compose installed
- [ ] SSH keys configured
- [ ] Firewall rules are set (allow 80, 443, restrict 5432)
- [ ] Server updates applied (`apt update && apt upgrade`)

## Security

- [ ] PostgreSQL password updated in `.env`
- [ ] Backend CORS restrictions configured (if needed)
- [ ] Rate limiting enabled
- [ ] HTTPS enforced (redirect HTTP → HTTPS)
- [ ] Security headers configured in nginx
- [ ] Database credentials stored in secrets manager (not in git)
- [ ] SSH key-based authentication only (no password login)
- [ ] Fail2ban or similar brute-force protection installed

## Configuration

- [ ] `.env` file created with production values:
  ```
  POSTGRES_PASSWORD=strong_random_password
  VITE_API_URL=https://your-domain.com
  ENVIRONMENT=production
  ```
- [ ] SSL certificates placed in `/etc/nginx/ssl/` or configured in nginx config
- [ ] Nginx configuration updated for production domain
- [ ] Backend logging level set to INFO (not DEBUG)

## Deployment

- [ ] Clone repository: `git clone <repo-url>`
- [ ] Run deployment script: `./deploy.sh production`
- [ ] OR manually run: `docker-compose -f docker-compose.production.yml up -d`
- [ ] Verify services are running: `docker-compose ps` (all should be "Up")
- [ ] Check database health: `docker-compose exec postgres pg_isready`
- [ ] Verify APIs respond:
  ```bash
  curl https://your-domain.com/health
  curl https://your-domain.com/tickers
  ```

## Post-Deployment

- [ ] Frontend loads successfully
- [ ] API endpoints respond
- [ ] No errors in logs: `docker-compose logs`
- [ ] Database is accessible
- [ ] SSL certificate is valid
- [ ] Test signal generation: `curl https://your-domain.com/signal/NPN`
- [ ] Monitor system resources (CPU, RAM, disk)

## Monitoring & Maintenance

- [ ] Set up log aggregation (e.g., ELK Stack, DataDog, Papertrail)
- [ ] Configure alerts for:
  - Service down
  - High CPU/RAM usage
  - Database connection errors
  - API response time > 5s
- [ ] Daily backup verification
- [ ] Weekly log review
- [ ] Monthly security updates
- [ ] Quarterly disaster recovery test

## Scaling (if needed)

- [ ] Backend can be scaled horizontally
- [ ] Use load balancer (nginx, HAProxy, cloud native)
- [ ] Database replication configured (for high availability)
- [ ] Redis cache layer added (optional)
- [ ] CDN configured for static assets

## Rollback Plan

- [ ] Previous version is tagged in git
- [ ] Database backup before each deployment
- [ ] Rollback procedure tested: `git checkout <tag> && ./deploy.sh`
- [ ] Rollback time target: < 10 minutes

## Documentation

- [ ] Deployment runbook created
- [ ] Emergency procedures documented
- [ ] Team trained on deployment process
- [ ] Access credentials securely shared
- [ ] Runbook location known by all ops team

---

**Deployment Status:** [ ] Ready for Production

**Deployed By:** ________________  
**Date:** ________________  
**Version/Commit:** ________________  

---

## Post-Deployment Support Contacts

- **On-Call Engineer:** [Name & Phone]
- **DBA:** [Name & Phone]
- **DevOps Lead:** [Name & Phone]
