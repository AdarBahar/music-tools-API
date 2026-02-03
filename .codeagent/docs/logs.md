# 📋 Application Logs Guide

This document describes where to find and how to access logs for the Music Tools API deployment.

**Legend:**
- 🖥️ **Server** = Run on your Hetzner server
- 👤 **apitools** = Run as the `apitools` user

---

## Log Locations Summary

| Log Type | Location | Description |
|----------|----------|-------------|
| App (stdout/stderr) | `journalctl -u music-tools-api` | Main application logs from Uvicorn/FastAPI |
| Nginx access | `/var/log/nginx/access.log` | All HTTP requests hitting Nginx |
| Nginx errors | `/var/log/nginx/error.log` | Nginx errors and warnings |
| Custom app logs | `/var/www/apitools/logs/` | Application-specific log files (if configured) |

---

## 1. Application Logs (systemd/journalctl)

The primary source for application logs when running via systemd.

🖥️ **Server** | 👤 **apitools** (with sudo)

### Follow logs in real-time
```bash
sudo journalctl -u music-tools-api -f
```

### View last N lines
```bash
# Last 100 lines
sudo journalctl -u music-tools-api -n 100

# Last 500 lines
sudo journalctl -u music-tools-api -n 500
```

### Filter by time
```bash
# Logs since today
sudo journalctl -u music-tools-api --since today

# Logs from specific time
sudo journalctl -u music-tools-api --since "2026-02-03 12:00:00"

# Logs between two times
sudo journalctl -u music-tools-api --since "2026-02-03 08:00:00" --until "2026-02-03 18:00:00"

# Logs from last hour
sudo journalctl -u music-tools-api --since "1 hour ago"
```

### Filter by priority/level
```bash
# Only errors
sudo journalctl -u music-tools-api -p err

# Errors and warnings
sudo journalctl -u music-tools-api -p warning
```

### Export logs to file
```bash
sudo journalctl -u music-tools-api --since today > /tmp/app-logs.txt
```

---

## 2. Nginx Logs

Nginx logs all incoming HTTP requests and errors.

🖥️ **Server** | 👤 **apitools** (with sudo)

### Access Logs (all requests)
```bash
# Follow in real-time
tail -f /var/log/nginx/access.log

# Last 100 lines
tail -n 100 /var/log/nginx/access.log

# Search for specific endpoint
grep "/api/v1/youtube" /var/log/nginx/access.log

# Search for specific IP
grep "192.168.1.100" /var/log/nginx/access.log

# Search for errors (4xx, 5xx)
grep -E " (4[0-9]{2}|5[0-9]{2}) " /var/log/nginx/access.log
```

### Error Logs
```bash
# Follow in real-time
tail -f /var/log/nginx/error.log

# Last 100 lines
tail -n 100 /var/log/nginx/error.log
```

### Combined real-time monitoring
```bash
tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

---

## 3. Custom Application Logs

If the application writes to custom log files.

🖥️ **Server** | 👤 **apitools**

### Check if logs directory exists
```bash
ls -la /var/www/apitools/logs/
```

### View custom logs
```bash
# List all log files
ls -la /var/www/apitools/logs/

# Follow all log files
tail -f /var/www/apitools/logs/*.log

# View specific log file
tail -f /var/www/apitools/logs/app.log
```

---

## 4. Useful Log Analysis Commands

🖥️ **Server** | 👤 **apitools** (with sudo)

### Count requests by endpoint
```bash
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20
```

### Count requests by IP
```bash
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20
```

### Count requests by status code
```bash
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn
```

### Find slow requests (if using combined log format)
```bash
awk '($NF > 1.0)' /var/log/nginx/access.log
```

### Monitor for errors in real-time
```bash
sudo journalctl -u music-tools-api -f | grep -i "error\|exception\|failed"
```

---

## 5. Log Rotation

Logs are automatically rotated by the system. Configuration is in:

```bash
# Nginx log rotation
cat /etc/logrotate.d/nginx

# Journald configuration
cat /etc/systemd/journald.conf
```

### Manual log cleanup (if needed)
```bash
# Clear old journald logs (keep last 7 days)
sudo journalctl --vacuum-time=7d

# Clear old journald logs (keep last 500MB)
sudo journalctl --vacuum-size=500M
```

---

## 6. Troubleshooting Common Issues

### Service not starting
```bash
sudo systemctl status music-tools-api
sudo journalctl -u music-tools-api -n 50 --no-pager
```

### 502 Bad Gateway
```bash
# Check if Uvicorn is running
sudo systemctl status music-tools-api

# Check Nginx error log
tail -n 50 /var/log/nginx/error.log
```

### High memory/CPU usage
```bash
# Check process resources
ps aux | grep uvicorn
top -p $(pgrep -f uvicorn)
```

### Connection refused errors
```bash
# Verify Uvicorn is listening on correct port
ss -tlnp | grep 8000
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Follow app logs | `sudo journalctl -u music-tools-api -f` |
| Last 100 app logs | `sudo journalctl -u music-tools-api -n 100` |
| Logs since today | `sudo journalctl -u music-tools-api --since today` |
| Follow Nginx access | `tail -f /var/log/nginx/access.log` |
| Follow Nginx errors | `tail -f /var/log/nginx/error.log` |
| Service status | `sudo systemctl status music-tools-api` |
| Restart service | `sudo systemctl restart music-tools-api` |
