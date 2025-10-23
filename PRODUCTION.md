# 🚀 Production Deployment Guide

This guide covers deploying the Discord Music Bot to production environments.

## 📋 Pre-Deployment Checklist

### 1. Environment Configuration

**Edit your `.env` file for production:**

```env
# REQUIRED: Your Discord bot token
BOT_TOKEN=your_actual_bot_token_here

# REMOVE THIS FOR PRODUCTION (leave empty)
# Guild ID is for development only - causes commands to sync globally (1 hour initial sync)
GUILD_ID=

# OPTIONAL: Your Discord user ID for owner-only commands
OWNER_ID=your_discord_user_id

# OPTIONAL: FFmpeg path (default works in Docker)
FFMPEG_PATH=ffmpeg

# OPTIONAL: Idle timeout in seconds (default: 5 minutes)
QUEUE_TIMEOUT=300
```

**⚠️ Important:**
- **Remove `GUILD_ID`** for production - this enables global command sync
- Commands take up to 1 hour to sync globally on first deployment
- Never commit `.env` to version control

### 2. Security Verification

- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has no real credentials
- [ ] Bot token is valid and from correct application
- [ ] Bot runs as non-root user (automatic in Docker)

### 3. Discord Bot Setup

**Required Intents (Developer Portal → Bot → Privileged Gateway Intents):**
- ✅ Message Content Intent (for some functionality)
- ✅ Server Members Intent (optional)

**Required Permissions:**
- Read Messages/View Channels
- Send Messages
- Connect (voice)
- Speak (voice)
- Use Slash Commands

**Permission Integer:** `3165184`

**Invite URL Format:**
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=3165184&scope=bot%20applications.commands
```

## 🐳 Docker Production Deployment

### Method 1: Docker Compose (Recommended)

**1. Start the bot:**
```bash
docker-compose up -d
```

**2. View logs:**
```bash
docker-compose logs -f music-bot
```

**3. Restart after config changes:**
```bash
docker-compose restart
```

**4. Stop the bot:**
```bash
docker-compose down
```

**5. Update and rebuild:**
```bash
git pull
docker-compose up -d --build
```

### Method 2: Manual Docker

**Build:**
```bash
docker build -t discord-music-bot:latest .
```

**Run:**
```bash
docker run -d \
  --name discord-music-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/cache:/app/cache:rw \
  discord-music-bot:latest
```

**View logs:**
```bash
docker logs -f discord-music-bot
```

## 🖥️ Linux Server Deployment

### systemd Service Setup

**1. Create service file:**
```bash
sudo nano /etc/systemd/system/discord-music-bot.service
```

**2. Add configuration:**
```ini
[Unit]
Description=Discord Music Bot
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/YuukiSourceCode
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-music-bot
sudo systemctl start discord-music-bot
```

**4. Manage service:**
```bash
# Check status
sudo systemctl status discord-music-bot

# View logs
sudo journalctl -u discord-music-bot -f

# Restart
sudo systemctl restart discord-music-bot

# Stop
sudo systemctl stop discord-music-bot
```

## 📊 Monitoring & Logging

### View Docker Logs
```bash
# Real-time logs
docker-compose logs -f music-bot

# Last 100 lines
docker-compose logs --tail=100 music-bot

# Since specific time
docker-compose logs --since 30m music-bot
```

### Log Rotation

Logs are automatically rotated (configured in `docker-compose.yml`):
- Max size: 10MB per file
- Max files: 3
- Total max space: ~30MB

### Health Checks

Built-in health check (every 30 seconds):
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' discord-music-bot
```

## 🔄 Updates & Maintenance

### Update Bot Code
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Update Dependencies
```bash
# Rebuild with latest packages
docker-compose build --no-cache
docker-compose up -d
```

### Backup Configuration
```bash
# Backup .env file (store securely)
cp .env .env.backup

# Backup cache (optional)
tar -czf cache_backup.tar.gz cache/
```

## ⚡ Performance Optimization

### Resource Limits

Current limits (in `docker-compose.yml`):
- **CPU Limit:** 2 cores max
- **Memory Limit:** 1GB max
- **CPU Reservation:** 0.5 cores
- **Memory Reservation:** 256MB

Adjust based on your server and usage:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Increase for more concurrent guilds
      memory: 2G     # Increase if bot handles many large queues
    reservations:
      cpus: '1'
      memory: 512M
```

### Cache Management

The `cache/` directory stores yt-dlp data:
- Mounted as volume in Docker
- Improves performance for repeated queries
- Can grow large over time

**Clean cache periodically:**
```bash
docker-compose down
rm -rf cache/*
docker-compose up -d
```

## 🐛 Troubleshooting

### Bot Won't Start

**Check logs:**
```bash
docker-compose logs music-bot
```

**Common issues:**
- Invalid `BOT_TOKEN` in `.env`
- Missing `.env` file
- Port conflicts (shouldn't happen - bot doesn't expose ports)

### Commands Not Appearing

**If using fresh production deployment:**
- Global sync takes **up to 1 hour** on first deployment
- After that, commands are cached by Discord
- Try re-inviting bot with correct scopes

**Force resync:**
1. Set `GUILD_ID` to your test server temporarily
2. Restart bot
3. Test in that server (instant sync)
4. Remove `GUILD_ID` and restart for global

### Memory Issues

**If bot crashes with OOM:**
1. Increase memory limit in `docker-compose.yml`
2. Check for memory leaks in logs
3. Reduce `QUEUE_TIMEOUT` to free resources faster

### Audio Playback Issues

**FFmpeg errors:**
- Check FFmpeg is installed in container (should be automatic)
- Verify `FFMPEG_PATH` if using custom path

**yt-dlp extraction failures:**
- Update to latest version: rebuild Docker image
- Some videos may be restricted
- Check network connectivity from container

## 🔐 Security Hardening

### Environment Security
- ✅ Never commit `.env`
- ✅ Use environment secrets in CI/CD
- ✅ Rotate bot token periodically
- ✅ Limit bot permissions to minimum required

### Container Security
- ✅ Runs as non-root user (`botuser`)
- ✅ No exposed ports (outbound only)
- ✅ Minimal base image (Python slim)
- ✅ Regular updates

### Network Security
- Bot only needs outbound internet access
- No inbound ports required
- Firewall can block all inbound to bot container

## 📈 Scaling Considerations

### Multi-Guild Performance

The bot handles multiple guilds simultaneously:
- Per-guild state isolation
- Concurrent playback across servers
- Resource usage scales with active voice connections

### Horizontal Scaling

**Not recommended** - Discord bots use WebSocket connections:
- Each instance needs unique token
- Cannot load balance single bot across multiple instances
- Vertical scaling (more CPU/RAM) is preferred

### Vertical Scaling

If handling many guilds:
1. Increase CPU cores in `docker-compose.yml`
2. Increase memory limit
3. Use faster storage for cache
4. Deploy on dedicated server

## 🆘 Emergency Procedures

### Bot Misbehaving

**Immediate stop:**
```bash
docker-compose down
```

**Emergency token rotation:**
1. Regenerate token in Discord Developer Portal
2. Update `.env` with new token
3. Restart: `docker-compose up -d`

### Data Loss Prevention

**Before major changes:**
```bash
# Backup configuration
cp .env .env.backup_$(date +%Y%m%d)

# Backup cache
tar -czf cache_backup_$(date +%Y%m%d).tar.gz cache/
```

## ✅ Production Checklist

Before going live:

- [ ] `.env` configured with production values
- [ ] `GUILD_ID` removed from `.env`
- [ ] Bot token is valid
- [ ] Bot invited with correct permissions and scopes
- [ ] Docker Compose tested
- [ ] Logs accessible and readable
- [ ] Monitoring setup (optional)
- [ ] Backup procedures documented
- [ ] Emergency contacts listed

## 📞 Support

If issues persist:
1. Check logs: `docker-compose logs -f music-bot`
2. Verify configuration against this guide
3. Review main [README.md](README.md) troubleshooting section
4. Open GitHub issue with logs and configuration (redact sensitive data)

---

**Production deployment completed! Your bot should now be running 24/7.**
