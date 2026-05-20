# 🐳 Docker Commands

## Start All Services
```bash
docker-compose up
```

## Stop Services
```bash
docker-compose down
```

## Clean Reset (Remove all data)
```bash
docker-compose down -v
```

## View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db
```

## Rebuild Images
```bash
docker-compose build --no-cache
docker-compose up
```

## Access Container Terminal
```bash
# Frontend
docker exec -it financial_frontend sh

# Backend
docker exec -it financial_backend bash

# Database
docker exec -it financial_db psql -U user -d financial_db
```

## Services

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000/docs
- **Database**: localhost:5432 (user/password)

---

## Troubleshooting

### Port Already in Use
```bash
docker-compose down
docker-compose up
```

### Clear Everything & Start Fresh
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Check Docker is Running
```bash
docker ps
```

### View Container Status
```bash
docker-compose ps
```
