# 🚀 FastAPI Production Deployment on Hetzner (with User Isolation)

This guide walks you through deploying your FastAPI (Music Tools API) app on a Hetzner server, using a dedicated Linux user (`apitools`), Uvicorn, systemd, and Nginx for secure, robust, and maintainable production hosting.

**Legend:**
- 🖥️ **Server** = Run on your Hetzner server
- 💻 **Localhost** = Run on your local machine
- 👤 **root/sudo** = Requires root or sudo privileges
- 👤 **apitools** = Run as the `apitools` user

---

## 1. Create a Dedicated User

🖥️ **Server** | 👤 **root/sudo**

SSH into your Hetzner server as root or a sudo user:

```bash
sudo adduser apitools
# Set a strong password when prompted

# Add to sudoers if you want admin rights (optional):
sudo usermod -aG sudo apitools
```

### Enable SSH Access for apitools

**Option A: Password Authentication** (already enabled by default)

🖥️ **Server** | 👤 **root/sudo**

- Ensure `/etc/ssh/sshd_config` has `PasswordAuthentication yes`
- Restart SSH if you changed anything:
```bash
sudo systemctl restart sshd
```

**Option B: SSH Key Authentication (recommended)**

💻 **Localhost** | 👤 **your user**

Generate a key if you don't have one:
```bash
ssh-keygen -t ed25519 -C "apitools@hetzner"
```

Copy the public key to the server:
```bash
ssh-copy-id apitools@your-server-ip
```

Or manually add your public key:

🖥️ **Server** | 👤 **root/sudo**

```bash
sudo mkdir -p /home/apitools/.ssh
sudo nano /home/apitools/.ssh/authorized_keys
# Paste your public key (from ~/.ssh/id_ed25519.pub or ~/.ssh/id_rsa.pub)
sudo chown -R apitools:apitools /home/apitools/.ssh
sudo chmod 700 /home/apitools/.ssh
sudo chmod 600 /home/apitools/.ssh/authorized_keys
```

Now you can SSH/SCP as `apitools`:

💻 **Localhost** | 👤 **your user**

```bash
ssh apitools@your-server-ip
scp music-tools-api-dist.zip apitools@your-server-ip:/tmp-apitools/
```

---

## 1.5 Create Required Directories

🖥️ **Server** | 👤 **root/sudo**

Create the upload and deployment directories, and set ownership for `apitools`:

```bash
# Create directories
sudo mkdir -p /tmp-apitools
sudo mkdir -p /var/www/apitools

# Set ownership to apitools user
sudo chown apitools:apitools /tmp-apitools
sudo chown apitools:apitools /var/www/apitools

# Set permissions
sudo chmod 755 /tmp-apitools
sudo chmod 755 /var/www/apitools
```

**Directory purposes:**
- `/tmp-apitools` — Upload location for dist zip files (via SCP)
- `/var/www/apitools` — Deployment folder for the running app

---

## 2. Prepare the Environment

🖥️ **Server** | 👤 **root/sudo**

Switch to the new user:
```bash
su - apitools
```

🖥️ **Server** | 👤 **apitools** (with sudo)

Update and install dependencies:
```bash
sudo apt update && sudo apt upgrade -y
```

### Check Available Python Version

```bash
python3 --version
```

**If Python 3.10+ is already installed** (e.g., Python 3.11, 3.12), use the system Python:
```bash
sudo apt install python3-venv python3-pip nginx unzip git ffmpeg -y
```

**If you need Python 3.10 specifically** (e.g., on older Ubuntu), add the deadsnakes PPA:
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev nginx unzip git ffmpeg -y
```

> **Note:** Most modern Hetzner images (Ubuntu 22.04+, Debian 12+) ship with Python 3.10 or newer. Use whatever version is available (3.10, 3.11, 3.12 all work).

---

## 2.5 Configure Swap Space (Required for Stem Separation)

🖥️ **Server** | 👤 **apitools** (with sudo)

Demucs stem separation requires **4-8GB RAM** depending on the model. If your server has less than 4GB RAM, you **must** add swap space to prevent OOM (Out of Memory) kills.

### Check Current Memory and Swap

```bash
free -h
```

### Create Swap File (4GB recommended)

```bash
# Create 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Verify swap is active
free -h
```

### Make Swap Permanent

```bash
# Add to fstab so swap persists after reboot
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Optimize Swap Settings (Optional)

```bash
# Reduce swappiness (use RAM first, swap only when needed)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

> **Memory Requirements by Demucs Model:**
> | Model | RAM Required | Quality | Speed |
> |-------|-------------|---------|-------|
> | `htdemucs` | ~3-4GB | Good | Fast |
> | `htdemucs_ft` | ~5-8GB | Best | Slower |
> | `mdx_extra` | ~4-5GB | Good | Medium |
> | `mdx_extra_q` | ~4-5GB | Good (quantized) | Medium |
>
> **Recommendation:** Use `htdemucs` on servers with <4GB RAM + swap. Use `htdemucs_ft` only on servers with 8GB+ RAM.

### Pre-download Demucs Models (Optional)

Pre-downloading models reduces peak memory usage during first requests:

```bash
cd /var/www/apitools
source venv/bin/activate

# Download the default model
python -c "import torch; from demucs.pretrained import get_model; get_model('htdemucs')"

# Download the fine-tuned model (requires more RAM)
python -c "import torch; from demucs.pretrained import get_model; get_model('htdemucs_ft')"
```

---

## 3. Upload and Extract Your App

💻 **Localhost** | 👤 **your user**

Upload your `music-tools-api-dist.zip` to `/tmp-apitools/` using SCP:

```bash
scp music-tools-api-dist.zip apitools@your-server-ip:/tmp-apitools/
```

💻 **Localhost** | 👤 **your user**

SSH into the server:
```bash
ssh apitools@your-server-ip
```

🖥️ **Server** | 👤 **apitools**

Extract to the deployment folder:
```bash
cd /tmp-apitools
unzip music-tools-api-dist.zip -d /var/www/apitools
cd /var/www/apitools
```

---

## 4. Set Up Python Virtual Environment

🖥️ **Server** | 👤 **apitools**

Use the Python version available on your system (check with `python3 --version`):

```bash
cd /var/www/apitools
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# If stem separation fails with "TorchCodec is required", install torchcodec:
# pip install torchcodec
```

---

## 5. Test Uvicorn Manually

🖥️ **Server** | 👤 **apitools**

```bash
source /var/www/apitools/venv/bin/activate
cd /var/www/apitools
uvicorn main:app --host=0.0.0.0 --port=8000
```

### Open Firewall for Testing

🖥️ **Server** | 👤 **apitools** (with sudo)

```bash
# Allow ports temporarily for testing
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
sudo ufw status
```

💻 **Localhost** | 👤 **your user**

Test the endpoint:
```bash
curl http://your-server-ip:8000/health
```
- If successful, you'll get a JSON response.
- Press `CTRL+C` on the server to stop Uvicorn.

---

## 6. Create a systemd Service

🖥️ **Server** | 👤 **root/sudo**

Create the service file:
```bash
sudo nano /etc/systemd/system/music-tools-api.service
```

Paste the following:

```ini
[Unit]
Description=Music Tools API (FastAPI/Uvicorn)
After=network.target

[Service]
User=apitools
Group=apitools
WorkingDirectory=/var/www/apitools
Environment="PATH=/var/www/apitools/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080"
## Optional: restrict Demucs models on this server only
# Environment="DEMUCS_MODELS_ALLOWLIST=htdemucs"
ExecStart=/var/www/apitools/venv/bin/uvicorn main:app --host=127.0.0.1 --port=8000
Restart=always

[Install]
WantedBy=multi-user.target
```

> **Note:** We use `--host=127.0.0.1` because Nginx will handle external traffic. The PATH includes system directories so the service can find `ffmpeg`. The `ALLOWED_ORIGINS` setting enables CORS for frontend applications (add your production frontend URL if needed).

Enable and start the service:

🖥️ **Server** | 👤 **apitools** (with sudo)

```bash
sudo systemctl daemon-reload
sudo systemctl enable music-tools-api
sudo systemctl start music-tools-api
sudo systemctl status music-tools-api
```

---

## 7. Configure Nginx as a Reverse Proxy

🖥️ **Server** | 👤 **root/sudo**

Create the Nginx config:
```bash
sudo nano /etc/nginx/sites-available/music-tools-api
```

Paste the following configuration. **Note:** CORS is handled by FastAPI via the `ALLOWED_ORIGINS` environment variable, so Nginx just proxies requests cleanly.

```nginx
# HTTP to HTTPS redirect (managed by Certbot)
server {
    listen 80;
    server_name apitools.bahar.co.il;

    if ($host = apitools.bahar.co.il) {
        return 301 https://$host$request_uri;
    }

    return 404;
}

# HTTPS server
server {
    listen 443 ssl;
    server_name apitools.bahar.co.il;

    # SSL (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/apitools.bahar.co.il/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/apitools.bahar.co.il/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Allow large file uploads (100MB for audio files)
    client_max_body_size 100M;

    # Logging
    access_log /var/log/nginx/music-tools-api-access.log;
    error_log /var/log/nginx/music-tools-api-error.log;

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # YouTube info (lightweight)
    location /api/v1/youtube-info {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # YouTube to MP3 (heavy operation)
    location /api/v1/youtube-to-mp3 {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_connect_timeout 30s;
        proxy_send_timeout 600s;
    }

    # Stem separation (heavy operation - file upload)
    location /api/v1/separate-stems {
        proxy_pass http://127.0.0.1:8000;
        # Use HTTP/1.1 to support streaming uploads (chunked) when request buffering is disabled.
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 1800s;  # 30 min for stem separation
        proxy_connect_timeout 30s;
        proxy_send_timeout 300s;
        proxy_request_buffering off;
        proxy_buffering off;
    }

    # Models list
    location /api/v1/models {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Formats list
    location /api/v1/formats {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # File downloads
    location /api/v1/download {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    # Stats endpoint
    location /api/v1/stats {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Catch-all for remaining API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Default location
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the config and restart Nginx:

🖥️ **Server** | 👤 **apitools** (with sudo)

```bash
sudo ln -s /etc/nginx/sites-available/music-tools-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

> **Configuration Features:**
> - ✅ Automatic HTTP → HTTPS redirect
> - ✅ SSL managed by Certbot (auto-renewal)
> - ✅ Large file upload support (100MB) for audio processing
> - ✅ Extended timeouts for heavy operations (stem separation: 30 min)
> - ✅ Disabled buffering for file uploads/downloads
> - ✅ CORS handled by FastAPI (via `ALLOWED_ORIGINS` env var)

💻 **Localhost** | 👤 **your user**

Test via Nginx (HTTP):
```bash
curl http://apitools.bahar.co.il/health
```

---

## 8. Set Up SSL with Let's Encrypt

🖥️ **Server** | 👤 **apitools** (with sudo)

Install Certbot (if not already installed):
```bash
sudo apt install certbot python3-certbot-nginx -y
```

Request the SSL certificate:
```bash
sudo certbot --nginx -d apitools.bahar.co.il
```

> **Important:** Make sure your domain DNS points to your Hetzner server IP.

Certbot will automatically:
- Obtain the certificate
- Update your Nginx config for HTTPS
- Set up auto-renewal

---

## 9. Secure Firewall (Close Testing Ports)

🖥️ **Server** | 👤 **apitools** (with sudo)

After SSL is working, close unnecessary ports:

```bash
# Remove the testing port (8000)
sudo ufw delete allow 8000/tcp

# Verify final firewall rules
sudo ufw status
```

**Your final firewall should only allow:**
- `22/tcp` — SSH
- `80/tcp` — HTTP (redirects to HTTPS)
- `443/tcp` — HTTPS

Expected output:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
80/tcp (v6)                ALLOW       Anywhere (v6)
443/tcp (v6)               ALLOW       Anywhere (v6)
```

---

## 10. Test Your Deployment

💻 **Localhost** | 👤 **your user**

Test HTTPS endpoint:
```bash
curl https://apitools.bahar.co.il/health
```

Test API with authentication:
```bash
curl -H "X-API-Key: your-api-key" \
     -X POST https://apitools.bahar.co.il/api/v1/youtube-to-mp3 \
     -H "Content-Type: application/json" \
     -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
```

🖥️ **Server** | 👤 **apitools** (with sudo)

Check service logs:
```bash
sudo journalctl -u music-tools-api -f
```

Check Nginx logs:
```bash
tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

---

## 11. Security & Maintenance

### API Documentation Access
- Interactive documentation (`/docs`, `/redoc`) is disabled on production servers by default
- Set `DEBUG=true` only in development environments
- In production with `DEBUG=false`, API documentation endpoints are not mounted (you will see 404 Not Found)
- Use client libraries or API integration guides for production integrations

### Server-only model restriction (recommended)

If your server is RAM/disk constrained, you can disable heavy Demucs models **only on the server** via systemd.

🖥️ **Server** | 👤 **root/sudo**

Preferred (drop-in override; survives package/file updates):

```bash
sudo systemctl edit music-tools-api
```

In the editor, add:

```ini
[Service]
Environment="DEMUCS_MODELS_ALLOWLIST=htdemucs"
```

Then apply:

```bash
sudo systemctl daemon-reload
sudo systemctl restart music-tools-api
```

Verify:

```bash
curl -s https://apitools.bahar.co.il/api/v1/models
```

### Firewall Best Practices
- Only open ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Port 8000 should **never** be open in production
- Nginx reverse proxy ensures internal-only communication with Uvicorn

### Regular Maintenance

🖥️ **Server** | 👤 **apitools** (with sudo)

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Check SSL certificate renewal
sudo certbot renew --dry-run

# View service status
sudo systemctl status music-tools-api

# Restart service after updates
sudo systemctl restart music-tools-api
```

### Security Checklist
- ✅ Use SSH keys instead of passwords
- ✅ Keep system and Python packages updated
- ✅ Rotate API keys regularly
- ✅ Monitor logs for suspicious activity
- ✅ Use strong passwords for all users
- ✅ Ensure SSL certificate auto-renews

---

## Quick Reference Commands

| Action | Command | User |
|--------|---------|------|
| Start service | `sudo systemctl start music-tools-api` | apitools (sudo) |
| Stop service | `sudo systemctl stop music-tools-api` | apitools (sudo) |
| Restart service | `sudo systemctl restart music-tools-api` | apitools (sudo) |
| View logs | `sudo journalctl -u music-tools-api -f` | apitools (sudo) |
| Check status | `sudo systemctl status music-tools-api` | apitools (sudo) |
| Reload Nginx | `sudo systemctl reload nginx` | apitools (sudo) |
| Renew SSL | `sudo certbot renew` | apitools (sudo) |

---

**🎉 You now have a secure, isolated, production-grade FastAPI deployment on Hetzner!**

---

## Automated Deployment Script

For subsequent deployments, use the automated deploy script:

💻 **Localhost** | 👤 **your user**

```bash
# From the project root
./scripts/deploy.sh
```

The script will:
1. Create a distribution tarball (excluding venv, cache, etc.)
2. Upload to `/tmp-apitools` on the server
3. Backup the current deployment
4. Deploy new files to `/var/www/apitools`
5. Install/update Python dependencies
6. Restart the systemd service
7. Verify health check
8. Log the deployment

**Prerequisites:**
- SSH config with `Host apitools` pointing to your server
- `apitools` user with sudo access on the server
- Initial deployment completed (venv created, systemd configured)

---

## Troubleshooting

### OOM Kill (Out of Memory)

**Symptom:** Stem separation fails with "oom-kill" in logs:
```
music-tools-api.service: A process of this unit has been killed by the OOM killer.
music-tools-api.service: Failed with result 'oom-kill'.
```

**Solutions:**
1. **Add swap space** (see Section 2.5)
2. **Use a lighter model** — Select `htdemucs` instead of `htdemucs_ft`
3. **Upgrade server RAM** — 4GB+ recommended for stem separation

### Check Memory Status

```bash
# View memory and swap usage
free -h

# View detailed memory info
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree)"

# Monitor memory in real-time
watch -n 1 free -h

```

### No Space Left on Device (Disk Full)

**Symptom:** Stem separation fails after a long run with:
`RuntimeError: ... No space left on device`

Demucs writes **temporary WAV stems** into `/var/www/apitools/temp` before conversion. Even if the input file is small (e.g. 11MB MP3), the temporary WAV outputs can be **hundreds of MB to multiple GB** depending on track duration.

**Check disk usage:**
```bash
df -h
sudo du -sh /var/www/apitools/temp /var/www/apitools/outputs /var/www/apitools/uploads || true
```

**Quick cleanup (safe):**
```bash
sudo find /var/www/apitools/temp -mindepth 1 -maxdepth 1 -type d -mtime +1 -exec rm -rf {} +
sudo find /var/www/apitools/outputs -mindepth 1 -maxdepth 1 -type d -mtime +2 -exec rm -rf {} +
```

**Recommendation:** Keep **at least 3–5GB free** for `htdemucs_ft` jobs. Use `htdemucs` on smaller disks.

### Service Won't Start

```bash
# Check service status
sudo systemctl status music-tools-api

# View recent logs
sudo journalctl -u music-tools-api -n 50 --no-pager

# Check for Python errors
sudo journalctl -u music-tools-api | grep -i error
```

### CORS Errors

If you see CORS errors from a frontend:

1. Verify `ALLOWED_ORIGINS` in systemd service includes your frontend URL
2. Restart the service after changes:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart music-tools-api
   ```

### 413 Request Entity Too Large

Nginx is blocking large file uploads:

```bash
# Check current client_max_body_size in nginx config
grep client_max_body_size /etc/nginx/sites-available/music-tools-api

# Should be: client_max_body_size 100M;
```

### SSL Certificate Issues

```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# Check certificate expiry
sudo certbot certificates
```
