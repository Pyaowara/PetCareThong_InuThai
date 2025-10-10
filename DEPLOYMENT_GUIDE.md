# Google Compute Engine Deployment Guide

## Overview
Deploy your complete PetCare application (PostgreSQL, MinIO, Django Backend, SvelteKit Frontend) on a single Google Compute Engine VM using Google Cloud Console.

## Prerequisites
- Google Cloud account with billing enabled
- Domain name (optional)

## Step 1: Create Firewall Rules (Google Cloud Console)

1. **Open Google Cloud Console:** https://console.cloud.google.com
2. **Navigate to VPC Network > Firewall:**
   - Go to the hamburger menu (☰) → VPC network → Firewall
3. **Create Firewall Rule for HTTP/App Ports:**
   - Click "CREATE FIREWALL RULE"
   - Name: `petcare-http`
   - Direction: `Ingress`
   - Action: `Allow`
   - Targets: `Specified target tags`
   - Target tags: `petcare-app`
   - Source IP ranges: `0.0.0.0/0`
   - Protocols and ports: `Specified protocols and ports`
   - Check `TCP` and enter ports: `80,3000,8000,9000,9001`
   - Click "CREATE"

4. **Create Firewall Rule for HTTPS:**
   - Click "CREATE FIREWALL RULE"
   - Name: `petcare-https`
   - Direction: `Ingress`
   - Action: `Allow`
   - Targets: `Specified target tags`
   - Target tags: `petcare-app`
   - Source IP ranges: `0.0.0.0/0`
   - Protocols and ports: `Specified protocols and ports`
   - Check `TCP` and enter ports: `443`
   - Click "CREATE"

## Step 2: Create Compute Engine Instance

1. **Navigate to Compute Engine:**
   - Go to hamburger menu (☰) → Compute Engine → VM instances
   - If prompted, enable the Compute Engine API

2. **Create VM Instance:**
   - Click "CREATE INSTANCE"
   
3. **Configure Instance:**
   - **Name:** `petcare-vm`
   - **Region:** `us-central1` (or your preferred region)
   - **Zone:** `us-central1-a` (or your preferred zone)
   - **Machine Configuration:**
     - Series: `E2`
     - Machine type: `e2-standard-2` (2 vCPU, 8 GB memory)
   
4. **Boot Disk Configuration:**
   - Click "CHANGE" under Boot disk
   - Operating system: `Ubuntu`
   - Version: `Ubuntu 20.04 LTS`
   - Boot disk type: `Standard persistent disk`
   - Size: `30 GB`
   - Click "SELECT"

5. **Firewall:**
   - Check both:
     - ☑️ Allow HTTP traffic
     - ☑️ Allow HTTPS traffic

6. **Advanced Options:**
   - Click "Advanced options"
   - Go to "Networking" tab
   - Under "Network tags" add: `petcare-app`

7. **Create the Instance:**
   - Click "CREATE"
   - Wait for the instance to be created (green checkmark)

## Step 3: Get VM External IP

1. **Find your VM in the instances list**
2. **Note the External IP** (e.g., `34.123.45.67`)
3. **Write down this IP** - you'll need it for configuration

## Step 4: Update Environment Configuration

1. **On your local computer, open the project folder**
2. **Copy the production environment file:**
   - Copy `.env.production` file and rename it to `.env`
3. **Edit the `.env` file:**
   - Open `.env` in a text editor
   - Replace every instance of `YOUR_EXTERNAL_IP` with your actual VM IP (from Step 3)
   - Example: If your IP is `34.123.45.67`, change:
     ```
     ALLOWED_HOSTS=YOUR_EXTERNAL_IP,your-domain.com,localhost,127.0.0.1,backend
     ```
     to:
     ```
     ALLOWED_HOSTS=34.123.45.67,your-domain.com,localhost,127.0.0.1,backend
     ```
   - Do the same for:
     - `CORS_ALLOW_ORIGIN=http://YOUR_EXTERNAL_IP,https://your-domain.com`
     - `VITE_API_BASE_URL=http://YOUR_EXTERNAL_IP:8000`
     - `PUBLIC_API_BASE_URL=http://YOUR_EXTERNAL_IP:8000`

## Step 5: Upload Project to VM

### Option A: Using Google Cloud Console (Recommended)

1. **Open Cloud Shell:**
   - In Google Cloud Console, click the Cloud Shell icon (>_) in the top toolbar
   - This opens a terminal in your browser

2. **Upload your project:**
   - In Cloud Shell, click the "Upload file" button (folder icon)
   - Create a zip file of your entire project on your computer first
   - Upload the zip file to Cloud Shell
   - In Cloud Shell, run:
     ```bash
     unzip your-project-name.zip
     ```

3. **Copy to your VM:**
   ```bash
   gcloud compute scp --recurse ./PetCareThong_InuThai petcare-vm:~/petcare --zone=us-central1-a
   ```

### Option B: Using Git (Alternative)

1. **Push your code to GitHub/GitLab** (if not already done)
2. **SSH into your VM** (see next step)
3. **Clone your repository on the VM:**
   ```bash
   git clone https://github.com/Pyaowara/PetCareThong_InuThai.git petcare
   ```

## Step 6: Connect to VM

1. **In Google Cloud Console, go to Compute Engine → VM instances**
2. **Find your `petcare-vm` instance**
3. **Click "SSH" button** in the Connect column
4. **A new browser window opens with terminal access to your VM**

## Step 7: Setup VM (Run these commands in the SSH terminal)

**Copy and paste each command one by one:**

1. **Update system:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Install Docker Compose:**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Logout and login again:**
   ```bash
   exit
   ```
   - Click "SSH" button again to reconnect
   - This applies the Docker group permissions

## Step 8: Deploy Application

1. **Navigate to project directory:**
   ```bash
   cd ~/petcare
   ```

2. **Verify files are uploaded:**
   ```bash
   ls -la
   ```
   You should see folders: `frontend/`, `petcare/`, `docker/`, etc.

3. **Build and start all services:**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d --build
   ```
   This will take 5-10 minutes to download images and build containers.

4. **Check if all services are running:**
   ```bash
   docker-compose -f docker/docker-compose.yml ps
   ```
   All services should show "Up" status.

5. **View logs to check for errors:**
   ```bash
   docker-compose -f docker/docker-compose.yml logs -f
   ```
   Press `Ctrl+C` to exit log viewing.

## Step 9: Initial Setup

1. **Create Django superuser:**
   ```bash
   docker-compose -f docker/docker-compose.yml exec backend python manage.py createsuperuser
   ```
   Follow the prompts to create admin username, email, and password.

2. **Test MinIO setup:**
   ```bash
   docker-compose -f docker/docker-compose.yml logs minio
   ```
   Should show MinIO started successfully.

## Step 10: Access Your Application

Replace `YOUR_EXTERNAL_IP` with your actual VM IP from Step 3:

- **🌐 Frontend (Main App):** `http://YOUR_EXTERNAL_IP:3000`
- **🔧 Backend API:** `http://YOUR_EXTERNAL_IP:8000/api/`
- **👨‍💼 Admin Panel:** `http://YOUR_EXTERNAL_IP:8000/admin/`
- **📁 MinIO Console:** `http://YOUR_EXTERNAL_IP:9001` 
  - Username: `minioadmin`
  - Password: `minioadmin123`

### Test Your Application:
1. **Open the frontend URL** in your browser
2. **Try to register a new account** or login
3. **Access the admin panel** with your superuser account
4. **Check that all features work** (appointments, pets, etc.)

## Step 11: Verify Everything is Working

1. **Check all containers are running:**
   ```bash
   docker ps
   ```

2. **Test database connection:**
   ```bash
   docker-compose -f docker/docker-compose.yml exec backend python manage.py check
   ```

3. **Check frontend build:**
   ```bash
   docker-compose -f docker/docker-compose.yml logs frontend
   ```

If you see any errors, check the troubleshooting section below.

## Production Optimizations (Optional)

### Setup Nginx Reverse Proxy (Optional - for single port access)

If you want to access everything through port 80 instead of different ports:

1. **Install Nginx:**
   ```bash
   sudo apt install nginx -y
   ```

2. **Create Nginx configuration:**
   ```bash
   sudo tee /etc/nginx/sites-available/petcare << 'EOF'
   server {
       listen 80;
       server_name YOUR_DOMAIN_OR_IP;

       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /api/ {
           proxy_pass http://localhost:8000/api/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /admin/ {
           proxy_pass http://localhost:8000/admin/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   EOF
   ```

3. **Enable site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/petcare /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Setup Domain and SSL (Optional)

1. **Point your domain to the VM IP** in your domain registrar
2. **Install Certbot:**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```
3. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## Common Issues and Solutions

### ❌ Problem: "Cannot connect to application"
**Solution:**
1. Check firewall rules are created correctly
2. Verify VM has the correct network tags
3. Check if services are running: `docker ps`

### ❌ Problem: "Database connection failed"
**Solution:**
```bash
# Check PostgreSQL logs
docker-compose -f docker/docker-compose.yml logs postgres

# Test database connection
docker-compose -f docker/docker-compose.yml exec postgres psql -U postgres -d petcare
```

### ❌ Problem: "Frontend shows 'Loading...' forever"
**Solution:**
1. Check backend API is accessible: `http://YOUR_IP:8000/api/`
2. Verify environment variables in `.env` have correct IP
3. Check frontend logs: `docker-compose -f docker/docker-compose.yml logs frontend`

### ❌ Problem: "MinIO access denied"
**Solution:**
```bash
# Check MinIO logs
docker-compose -f docker/docker-compose.yml logs minio

# Restart MinIO service
docker-compose -f docker/docker-compose.yml restart minio
```

### ❌ Problem: "Permission denied" errors
**Solution:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER ~/petcare
```

### ❌ Problem: "Docker build fails"
**Solution:**
```bash
# Clean up Docker
docker system prune -a

# Rebuild containers
docker-compose -f docker/docker-compose.yml up -d --build --force-recreate
```

## Maintenance Commands

```bash
# Check application status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f [service_name]

# Restart services
docker-compose -f docker/docker-compose.yml restart

# Update application
cd ~/petcare
git pull  # if using git
docker-compose -f docker/docker-compose.yml up -d --build

# Backup database
docker-compose -f docker/docker-compose.yml exec postgres pg_dump -U postgres petcare > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose -f docker/docker-compose.yml exec -T postgres psql -U postgres petcare < backup_file.sql

# Clean up unused Docker resources
docker system prune -a
```

## Monitoring

```bash
# System resources
htop
df -h
free -h

# Docker resources
docker stats

# Application logs
docker-compose -f docker/docker-compose.yml logs --tail=100 -f

# Nginx logs (if using nginx)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Services won't start:
```bash
docker-compose -f docker/docker-compose.yml logs [service_name]
```

### Database connection issues:
```bash
docker-compose -f docker/docker-compose.yml exec postgres psql -U postgres -d petcare
```

### MinIO access issues:
```bash
docker-compose -f docker/docker-compose.yml logs minio
```

### Frontend not loading:
```bash
docker-compose -f docker/docker-compose.yml logs frontend
```

### Check network connectivity:
```bash
docker network ls
docker-compose -f docker/docker-compose.yml exec backend ping postgres
docker-compose -f docker/docker-compose.yml exec backend ping minio
```

## Security Recommendations

1. **Change default passwords** in `.env`
2. **Use strong passwords** for database and MinIO
3. **Setup firewall rules** for specific ports only
4. **Use HTTPS** in production
5. **Regular security updates:** `sudo apt update && sudo apt upgrade`
6. **Setup SSH key authentication** and disable password login
7. **Use fail2ban** to prevent brute force attacks

## Cost Optimization

1. **Use preemptible instances** for development (50-91% cheaper)
2. **Schedule automatic shutdown** during off-hours using Cloud Scheduler
3. **Use smaller machine types** if sufficient (e2-micro for testing)
4. **Setup automated backups** only for important data
5. **Monitor resource usage** and adjust instance size accordingly

---

Your PetCare application is now ready for production deployment on Google Compute Engine! 🚀