# 🐘 Docker Services for PetCare

PostgreSQL database + MinIO object storage for the PetCare application.

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Stop services
docker-compose down
```

## 📋 Services

### PostgreSQL Database
- **Port**: 5432
- **Database**: petcare
- **User**: postgres  
- **Password**: postgres

### MinIO Object Storage
- **API**: http://localhost:9000
- **Console**: http://localhost:9001
- **User**: minioadmin
- **Password**: minioadmin123

## 📊 Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart a service
docker-compose restart postgres
docker-compose restart minio

# Remove everything (including data)
docker-compose down -v
```

## 🔧 Data Storage

- **PostgreSQL**: Stored in `postgres_data` volume
- **MinIO**: Stored in `minio_data` volume

Data persists between container restarts.