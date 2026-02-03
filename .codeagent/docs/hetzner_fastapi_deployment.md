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
sudo apt install python3-venv python3-pip nginx unzip git -y
```

**If you need Python 3.10 specifically** (e.g., on older Ubuntu), add the deadsnakes PPA:
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev nginx unzip git -y
```

> **Note:** Most modern Hetzner images (Ubuntu 22.04+, Debian 12+) ship with Python 3.10 or newer. Use whatever version is available (3.10, 3.11, 3.12 all work).

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
Environment="PATH=/var/www/apitools/venv/bin"
ExecStart=/var/www/apitools/venv/bin/uvicorn main:app --host=127.0.0.1 --port=8000
Restart=always

[Install]
WantedBy=multi-user.target
```

> **Note:** We use `--host=127.0.0.1` because Nginx will handle external traffic.

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

Create the Nginx config with security hardening:
```bash
sudo nano /etc/nginx/sites-available/music-tools-api
```

Paste the following production-ready configuration with HTTP/2, HTTPS redirection, and security headers:

```nginx
# HTTP to HTTPS redirect (port 80)
server {
    listen 80;
    listen [::]:80;
    server_name apitools.bahar.co.il;

    # Allow Let's Encrypt ACME challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS primary server (port 443)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name apitools.bahar.co.il;

    # SSL Certificate configuration (set by Certbot)
    ssl_certificate /etc/letsencrypt/live/apitools.bahar.co.il/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/apitools.bahar.co.il/privkey.pem;

    # Security: TLS 1.2 and 1.3 only
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Logging
    access_log /var/log/nginx/music-tools-api-access.log;
    error_log /var/log/nginx/music-tools-api-error.log;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_light:10m rate=30r/m;
    limit_req_zone $binary_remote_addr zone=api_heavy:10m rate=5r/m;

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Light operations (info endpoints, downloads)
    location ~ ^/api/v1/(youtube-info|models|formats|stats|download) {
        limit_req zone=api_light burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Heavy operations (conversions, stem separation)
    location ~ ^/api/v1/(youtube-to-mp3|separate-stems) {
        limit_req zone=api_heavy burst=2 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_connect_timeout 10s;
    }

    # Catch-all for remaining API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API documentation (disabled in production)
    location ~ ^/(docs|redoc|openapi.json) {
        return 403;
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
sudo systemctl restart nginx
```

> **Security Features in This Configuration:**
> - ✅ Automatic HTTP → HTTPS redirect
> - ✅ TLS 1.2 and 1.3 only (no legacy protocols)
> - ✅ Strong cipher suites with ChaCha20-Poly1305 support
> - ✅ HSTS header (HTTP Strict Transport Security) for 1 year
> - ✅ X-Content-Type-Options, X-Frame-Options, and CSP headers
> - ✅ Rate limiting per endpoint type (light vs heavy operations)
> - ✅ API documentation endpoints (`/docs`, `/redoc`) disabled by default
> - ✅ Long proxy timeouts for heavy operations (stem separation)

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
- Interactive documentation (`/docs`, `/redoc`) is disabled on production servers
- Set `DEBUG=true` only in development environments
- In production with `DEBUG=false`, API documentation endpoints return 403 Forbidden
- Use client libraries or API integration guides for production integrations

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
