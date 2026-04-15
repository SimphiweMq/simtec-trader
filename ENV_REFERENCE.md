# Environment Variables Reference

## Backend Variables

### Required
- **DATABASE_URL** - PostgreSQL connection string
  ```
  postgresql://user:password@host:port/database
  ```

- **BACKEND_PORT** - Port to run the API on (default: 8002)
  ```
  8002
  ```

- **BACKEND_HOST** - Host to bind to (default: 0.0.0.0)
  ```
  0.0.0.0
  ```

### Optional
- **ENVIRONMENT** - Deployment environment (default: development)
  ```
  production  # Disables hot reload
  development # Enables hot reload
  ```

- **LOG_LEVEL** - Logging verbosity (default: INFO)
  ```
  DEBUG, INFO, WARNING, ERROR, CRITICAL
  ```

## Frontend Variables

### Required
- **VITE_API_URL** - Backend API base URL
  ```
  Development: http://localhost:8002
  Production: https://your-domain.com
  ```

### Optional
- **VITE_APP_TITLE** - Application title in browser (default: SIMTEK TRADER)

## Database Variables

- **POSTGRES_USER** - PostgreSQL username (default: simtek_user)
  ```
  simtek_user
  ```

- **POSTGRES_PASSWORD** - PostgreSQL password
  ```
  strong_random_password_min_20_chars
  ```

- **POSTGRES_DB** - Database name (default: simtek_trader)
  ```
  simtek_trader
  ```

## Docker Deployment

### docker-compose.yml
Uses variables from `.env` file for development or local testing.

### docker-compose.production.yml
Production configuration with additional security settings:
- Database not exposed to outside network
- No hot-reload for backend
- Environment set to production
- All services configured with `restart: always`

## Setting Variables

### Local Development
Create `.env` file in root directory:
```bash
cp .env.example .env
# Edit .env with your values
```

### Docker Compose
Variables automatically loaded from `.env`:
```bash
docker-compose up -d
```

### Production (Docker)
Set variables in `.env.production`:
```bash
cp .env.example .env.production
# Update with production values
docker-compose -f docker-compose.production.yml up -d
```

### Docker Build Arguments
Frontend API URL can be set as build argument:
```bash
docker build \
  -f Dockerfile.frontend \
  --build-arg VITE_API_URL=https://your-domain.com \
  -t simtek-frontend .
```

### Environment (native Python/Node)
Linux/macOS:
```bash
export DATABASE_URL="postgresql://..."
export BACKEND_PORT=8002
export ENVIRONMENT=production
python src/main.py
```

Windows (PowerShell):
```powershell
$env:DATABASE_URL="postgresql://..."
$env:BACKEND_PORT=8002
$env:ENVIRONMENT=production
python src/main.py
```

## Security Best Practices

1. **Never commit `.env` files** - use `.env.example` as template
2. **Use strong passwords** - minimum 20 characters with special chars
3. **Restrict DATABASE_URL** - use specific user with minimal permissions
4. **Rotate secrets** - change all passwords every 90 days
5. **Use secrets manager** - AWS Secrets, Azure KeyVault, or HashiCorp Vault
6. **Audit access** - log who accessed which credentials

## Production Deployment Environments

### AWS EC2
```bash
# In EC2 user data or deployment script
export DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id simtek/db/url --query SecretString --output text)
export ENVIRONMENT=production
docker-compose -f docker-compose.production.yml up -d
```

### Google Cloud Run
```bash
gcloud run deploy simtek-backend \
  --set-env-vars "DATABASE_URL=...,ENVIRONMENT=production"
```

### Heroku
```bash
heroku config:set DATABASE_URL="postgresql://..."
heroku config:set ENVIRONMENT="production"
```

### DigitalOcean Apps
Set in `.do/app.yaml`:
```yaml
envs:
  - key: DATABASE_URL
    value: ${DB_CONNECTION_STRING}
  - key: ENVIRONMENT
    value: production
```

## Validation

Test variables are correctly set:
```bash
# Backend health check
curl http://localhost:8002/health

# Frontend
curl http://localhost/

# Database
echo $DATABASE_URL
```

## Troubleshooting

**Error: Cannot connect to database**
- Verify `DATABASE_URL` format and credentials
- Check network connectivity to database host
- Ensure PostgreSQL is running

**Error: API not accessible from frontend**
- Verify `VITE_API_URL` is correct and accessible
- Check nginx proxy_pass configuration
- Verify CORS is enabled on backend

**Error: Services won't start**
- Check all required variables are set
- Verify no conflicting port assignments
- Check Docker is running: `docker ps`
