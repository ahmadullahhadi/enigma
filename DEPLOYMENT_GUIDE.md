# 🚀 Deployment Guide - Download-First Playback System

This guide covers deploying the Discord Music Bot with the new download-first playback system.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **FFmpeg**: Latest version installed and accessible
- **Storage**: At least 1GB free space for temporary audio files
- **Memory**: Minimum 512MB RAM (1GB+ recommended)
- **Network**: Stable internet connection for downloads

### Discord Setup
1. Create a Discord Application at https://discord.com/developers/applications
2. Create a bot user and copy the bot token
3. Enable the following bot permissions:
   - `Send Messages`
   - `Use Slash Commands`
   - `Connect` (Voice)
   - `Speak` (Voice)
   - `Use Voice Activity`
   - `Manage Channels` (Required for dynamic channel name updates)

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Required: Discord Bot Token
BOT_TOKEN=your_bot_token_here

# Optional: Guild ID for faster command syncing during development
GUILD_ID=

# Optional: Bot Owner ID
OWNER_ID=

# Optional: FFmpeg path (leave as 'ffmpeg' if in PATH)
FFMPEG_PATH=ffmpeg

# Optional: Idle timeout in seconds (default: 300)
QUEUE_TIMEOUT=300

# NEW: Download-first playback mode (recommended: true)
DOWNLOAD_FIRST_MODE=true

# NEW: Dynamic voice channel name updates (recommended: true)
CHANNEL_NAME_UPDATES=true
```

### Download-First Mode Configuration

#### Download-First Mode - Enabled (Recommended)
```env
DOWNLOAD_FIRST_MODE=true
```
**Benefits:**
- ✅ Eliminates playback speed issues
- ✅ Prevents audio cuts and skips
- ✅ Stable playback quality
- ✅ Immune to network fluctuations

**Requirements:**
- Additional storage space (~5-15MB per song during playback)
- Slightly longer initial loading time
- FFmpeg with audio processing capabilities

#### Channel Name Updates - Enabled (Recommended)
```env
CHANNEL_NAME_UPDATES=true
```
**Benefits:**
- ✅ Visual indication of currently playing track
- ✅ Automatic restoration of original names
- ✅ Smart handling of special characters
- ✅ Rate limit protection

**Requirements:**
- "Manage Channels" permission in voice channels
- Automatically disables if permissions are insufficient

#### Download-First Mode - Disabled (Legacy Mode)
```env
DOWNLOAD_FIRST_MODE=false
```
**Benefits:**
- ⚡ Faster song startup
- 💾 No additional storage requirements
- 🌐 Direct streaming from YouTube

**Drawbacks:**
- ⚠️ Potential playback speed issues
- ⚠️ Possible audio cuts/skips
- ⚠️ Network-dependent stability

#### Channel Name Updates - Disabled
```env
CHANNEL_NAME_UPDATES=false
```
**Use Cases:**
- 🔒 Servers where channel names should not be modified
- 🚫 Insufficient "Manage Channels" permissions
- 🏢 Corporate/formal Discord servers

**Note:** Feature automatically disables if bot lacks permissions

## 🐳 Docker Deployment (Recommended)

### Quick Start
```bash
# 1. Clone the repository
git clone <repository-url>
cd discord-music-bot

# 2. Create environment file
cp .env.example .env
# Edit .env with your bot token and settings

# 3. Deploy with Docker Compose
docker-compose up -d
```

### Docker Compose Configuration
The included `docker-compose.yml` is pre-configured for download-first mode:

```yaml
version: '3.8'
services:
  music-bot:
    build: .
    env_file: .env
    volumes:
      # Optional: Mount temp directory for better performance
      - ./temp_audio:/tmp/discord_bot_audio
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "pgrep", "-f", "python bot.py"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Storage Considerations
- **Container Storage**: Temporary files are stored in `/tmp/discord_bot_audio`
- **Volume Mounting**: Optional volume mount for better I/O performance
- **Auto-Cleanup**: Files are automatically deleted after playback

## 🖥️ Local Development

### Setup
```bash
# 1. Clone and navigate
git clone <repository-url>
cd discord-music-bot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run the bot
python bot.py
```

### Testing Download Functionality
```bash
# Test the download system
python test_download.py
```

This will verify:
- Download functionality
- File cleanup
- Streaming fallback
- Temporary directory management

## 🔧 Production Deployment

### System Service (Linux)

Create a systemd service file:

```ini
# /etc/systemd/system/discord-music-bot.service
[Unit]
Description=Discord Music Bot
After=network.target

[Service]
Type=simple
User=musicbot
WorkingDirectory=/opt/discord-music-bot
ExecStart=/opt/discord-music-bot/venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable discord-music-bot
sudo systemctl start discord-music-bot
sudo systemctl status discord-music-bot
```

### Process Manager (PM2)

```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'discord-music-bot',
    script: 'python',
    args: 'bot.py',
    cwd: '/path/to/bot',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      PYTHONUNBUFFERED: '1'
    }
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 📊 Monitoring and Maintenance

### Log Monitoring
```bash
# Docker logs
docker-compose logs -f music-bot

# Systemd logs
journalctl -u discord-music-bot -f

# PM2 logs
pm2 logs discord-music-bot
```

### Storage Monitoring
```bash
# Check temp directory usage
du -sh /tmp/discord_bot_audio

# Monitor disk space
df -h
```

### Health Checks
The bot includes built-in health monitoring:
- Process health checks
- Automatic cleanup on shutdown
- Graceful error handling
- Memory usage optimization

## 🛠️ Troubleshooting

### Common Issues

#### Download Failures
**Symptoms**: Songs fail to download, fall back to streaming
**Solutions**:
- Check internet connectivity
- Verify FFmpeg installation
- Ensure adequate disk space
- Check yt-dlp version

#### Storage Issues
**Symptoms**: "No space left on device" errors
**Solutions**:
- Monitor temp directory: `/tmp/discord_bot_audio`
- Increase available disk space
- Verify auto-cleanup is working
- Restart bot to clear orphaned files

#### FFmpeg Issues
**Symptoms**: Audio playback fails or distorted
**Solutions**:
- Verify FFmpeg installation: `ffmpeg -version`
- Update FFmpeg to latest version
- Check system PATH configuration
- Set explicit `FFMPEG_PATH` in .env

#### Permission Issues
**Symptoms**: Cannot create temp files
**Solutions**:
- Check temp directory permissions
- Ensure bot user has write access
- Verify Docker volume mounts
- Check SELinux/AppArmor policies

### Debug Mode
Enable detailed logging by setting environment variables:
```env
# Enable debug logging
PYTHONUNBUFFERED=1
LOG_LEVEL=DEBUG
```

### Performance Optimization

#### For High-Traffic Servers
```env
# Increase timeout for busy servers
QUEUE_TIMEOUT=600

# Use streaming mode for faster response
DOWNLOAD_FIRST_MODE=false
```

#### For Stability-Critical Deployments
```env
# Use download-first for maximum stability
DOWNLOAD_FIRST_MODE=true

# Increase timeout for download processing
QUEUE_TIMEOUT=900
```

## 🔄 Migration from Previous Versions

### Upgrading from v1.x
1. **Backup**: Save your current `.env` file
2. **Update**: Pull latest code changes
3. **Configure**: Add `DOWNLOAD_FIRST_MODE=true` to `.env`
4. **Test**: Run `python test_download.py`
5. **Deploy**: Restart the bot

### No Breaking Changes
- All existing commands work unchanged
- Previous configurations remain valid
- Automatic fallback to streaming mode
- Gradual migration supported

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Test with `python test_download.py`
4. Verify environment configuration
5. Check Discord bot permissions

Happy deploying! 🎵
