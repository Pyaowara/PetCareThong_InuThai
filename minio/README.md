# MinIO Docker Deployment

This repository contains the configuration to deploy MinIO using Docker Compose.

## What is MinIO?

MinIO is a high-performance, S3-compatible object storage system. It's designed for large-scale data infrastructure and is ideal for storing unstructured data such as photos, videos, log files, backups, and container/VM images.

## Prerequisites

- Docker installed on your system
- Docker Compose installed

## Quick Start

1. Clone or download this repository
2. Navigate to the project directory:
   ```bash
   cd minio
   ```

3. Start MinIO:
   ```bash
   docker-compose up -d
   ```

4. Access MinIO Console at: http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin123`

5. MinIO API is available at: http://localhost:9000

## Configuration

### Environment Variables

The `.env` file contains the following configuration:

- `MINIO_ROOT_USER`: The root username (default: minioadmin)
- `MINIO_ROOT_PASSWORD`: The root password (default: minioadmin123)

**Important**: Change the default credentials in the `.env` file before deploying to production!

### Ports

- **9000**: MinIO API port
- **9001**: MinIO Console (Web UI) port

### Data Persistence

MinIO data is stored in the `./data` directory on your host machine, which is mounted to `/data` inside the container. This ensures your data persists even if the container is restarted or recreated.

## Usage

### Starting MinIO
```bash
docker-compose up -d
```

### Stopping MinIO
```bash
docker-compose down
```

### Viewing Logs
```bash
docker-compose logs -f minio
```

### Accessing the Web Console

1. Open your browser and go to http://localhost:9001
2. Login with your credentials from the `.env` file
3. Create buckets and manage your objects through the web interface

### Using MinIO Client (mc)

You can use the MinIO client to interact with your MinIO server:

```bash
# Install MinIO client
docker run --rm -it --entrypoint=/bin/sh minio/mc

# Configure alias
mc alias set local http://localhost:9000 minioadmin minioadmin123

# Create a bucket
mc mb local/my-bucket

# Upload a file
mc cp myfile.txt local/my-bucket/
```

## Security Considerations

1. **Change default credentials**: Update `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` in the `.env` file
2. **Network security**: Consider using a reverse proxy with SSL/TLS for production deployments
3. **Access policies**: Configure appropriate access policies for your buckets and users

## Troubleshooting

### Container won't start
- Check if ports 9000 and 9001 are available
- Ensure Docker daemon is running
- Check logs: `docker-compose logs minio`

### Can't access web console
- Verify the container is running: `docker-compose ps`
- Check if ports are properly mapped: `docker port minio`
- Ensure firewall allows connections to ports 9000 and 9001

### Data not persisting
- Verify the `./data` directory exists and has proper permissions
- Check volume mounting in `docker-compose.yml`

## Production Deployment

For production use, consider:

1. Using Docker secrets for credentials
2. Setting up SSL/TLS encryption
3. Configuring backup strategies
4. Setting up monitoring and alerting
5. Using external volumes or cloud storage for data persistence
6. Implementing proper network security

## Resources

- [MinIO Documentation](https://docs.min.io/)
- [MinIO Docker Hub](https://hub.docker.com/r/minio/minio)
- [MinIO Client Documentation](https://docs.min.io/docs/minio-client-complete-guide.html)