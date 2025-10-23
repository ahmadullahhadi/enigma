# 🔍 Integration Checklist - Discord Music Bot v2.1.0

## 📋 Pre-Deployment Checklist

### ✅ Code Integration
- [x] **VoiceChannelManager class** implemented with all required methods
- [x] **GuildMusicState** enhanced with channel management functionality
- [x] **Track class** updated to support both download and streaming modes
- [x] **Music cog** integrated with channel name updates on all events
- [x] **Environment variables** added for both features
- [x] **Error handling** implemented for permissions and API limits
- [x] **Cleanup logic** added to all shutdown and disconnect events

### ✅ Configuration Files
- [x] **`.env.example`** updated with new configuration options
- [x] **`requirements.txt`** includes all necessary dependencies
- [x] **`docker-compose.yml`** compatible with new features
- [x] **`Dockerfile`** supports both download and channel management features

### ✅ Documentation
- [x] **`README.md`** updated with feature descriptions and setup
- [x] **`CHANGELOG.md`** documents all changes and improvements
- [x] **`DEPLOYMENT_GUIDE.md`** includes permission requirements
- [x] **`FEATURE_SUMMARY.md`** comprehensive overview of all features

### ✅ Testing
- [x] **`test_download.py`** validates download-first playback system
- [x] **`test_channel_names.py`** validates voice channel name updates
- [x] **Mock testing** for channel management without Discord dependency

---

## 🚀 Deployment Steps

### 1. Environment Setup
```bash
# Copy and configure environment
cp .env.example .env

# Required: Add your bot token
BOT_TOKEN=your_actual_bot_token_here

# Optional: Configure features
DOWNLOAD_FIRST_MODE=true
CHANNEL_NAME_UPDATES=true
```

### 2. Permission Verification
Ensure your Discord bot has these permissions:
- ✅ **Send Messages**
- ✅ **Use Slash Commands** 
- ✅ **Connect** (Voice)
- ✅ **Speak** (Voice)
- ✅ **Use Voice Activity**
- ✅ **Manage Channels** ← **NEW: Required for channel name updates**

### 3. Dependencies Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify FFmpeg installation
ffmpeg -version

# Verify yt-dlp installation
yt-dlp --version
```

### 4. Testing Phase
```bash
# Test download functionality
python test_download.py

# Test channel name functionality  
python test_channel_names.py

# Start bot in test mode
python bot.py
```

---

## 🧪 Functional Testing

### Download-First Playback System
- [ ] **Single Track Download**: `/play never gonna give you up`
- [ ] **Playlist Download**: `/play https://youtube.com/playlist?list=...`
- [ ] **Fallback to Streaming**: Test with unavailable video
- [ ] **File Cleanup**: Verify temp files are deleted after playback
- [ ] **Error Handling**: Test with network issues

### Dynamic Channel Names
- [ ] **Name Update on Play**: Channel shows `🎵 Song Title`
- [ ] **Name Restoration on Stop**: Channel reverts to original name
- [ ] **Special Character Handling**: Test with songs containing `<>:"/\|?*`
- [ ] **Long Title Truncation**: Test with very long song titles
- [ ] **Permission Handling**: Test without "Manage Channels" permission
- [ ] **Rate Limit Protection**: Test rapid song changes

### Integration Testing
- [ ] **Both Features Enabled**: Test download + channel names together
- [ ] **Mixed Mode**: Some tracks downloaded, some streamed
- [ ] **Multi-Guild**: Test with bot in multiple servers
- [ ] **Concurrent Playback**: Test multiple guilds playing simultaneously
- [ ] **Bot Restart**: Verify cleanup on restart
- [ ] **Graceful Shutdown**: Test proper cleanup on shutdown

---

## 🔧 Configuration Validation

### Environment Variables
```bash
# Verify all variables are set correctly
echo "Bot Token: ${BOT_TOKEN:0:10}..." 
echo "Download Mode: $DOWNLOAD_FIRST_MODE"
echo "Channel Updates: $CHANNEL_NAME_UPDATES"
echo "FFmpeg Path: $FFMPEG_PATH"
```

### File Permissions
```bash
# Check temp directory permissions
ls -la /tmp/discord_bot_audio/
# Should be writable by bot user

# Check log file permissions (if using)
ls -la bot.log
# Should be writable by bot user
```

### Network Connectivity
```bash
# Test YouTube connectivity
yt-dlp --list-formats "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Test Discord API connectivity
curl -H "Authorization: Bot $BOT_TOKEN" https://discord.com/api/v10/users/@me
```

---

## 📊 Performance Monitoring

### Resource Usage
- [ ] **Memory Usage**: Monitor RAM consumption during operation
- [ ] **Disk Usage**: Check temp directory size during downloads
- [ ] **CPU Usage**: Monitor during download and playback phases
- [ ] **Network Usage**: Track bandwidth consumption

### API Rate Limits
- [ ] **Discord API**: Monitor for rate limit warnings
- [ ] **YouTube API**: Check for extraction failures
- [ ] **Channel Renames**: Verify 10-second cooldown is working

### Error Monitoring
- [ ] **Download Failures**: Track and log failed downloads
- [ ] **Permission Errors**: Monitor channel rename permission issues
- [ ] **Playback Errors**: Track audio playback failures
- [ ] **Cleanup Errors**: Monitor temp file cleanup issues

---

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Channel names not updating
**Symptoms**: Voice channel names remain unchanged during playback
**Diagnosis**:
```bash
# Check bot permissions
# Check logs for permission errors
# Verify CHANNEL_NAME_UPDATES=true
```
**Solutions**:
- Grant "Manage Channels" permission to bot
- Enable feature in environment variables
- Check bot is actually in voice channel

#### Issue: Downloads failing
**Symptoms**: All tracks fall back to streaming mode
**Diagnosis**:
```bash
# Test yt-dlp directly
yt-dlp --extract-audio "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Check disk space
df -h

# Check FFmpeg
ffmpeg -version
```
**Solutions**:
- Update yt-dlp: `pip install --upgrade yt-dlp`
- Free up disk space
- Install/update FFmpeg

#### Issue: Rate limit errors
**Symptoms**: "Rate limited" or "Too Many Requests" errors
**Diagnosis**:
```bash
# Check logs for rate limit messages
# Monitor API request frequency
```
**Solutions**:
- Built-in cooldowns should prevent this
- Check for multiple bot instances
- Verify Discord API status

---

## ✅ Go-Live Checklist

### Final Verification
- [ ] **Bot starts without errors**
- [ ] **All slash commands register properly**
- [ ] **Voice connection works**
- [ ] **Download system functional**
- [ ] **Channel name updates working**
- [ ] **Cleanup processes working**
- [ ] **Error handling graceful**
- [ ] **Documentation complete**

### Production Deployment
- [ ] **Environment configured for production**
- [ ] **Monitoring systems in place**
- [ ] **Backup procedures established**
- [ ] **Update procedures documented**
- [ ] **Support contacts identified**

### Post-Deployment
- [ ] **Monitor logs for first 24 hours**
- [ ] **Verify all features working in production**
- [ ] **Check resource usage patterns**
- [ ] **Gather user feedback**
- [ ] **Document any issues encountered**

---

## 📞 Support Information

### Log Locations
- **Bot Logs**: Console output or `bot.log`
- **Docker Logs**: `docker-compose logs music-bot`
- **System Logs**: `/var/log/` (Linux) or Event Viewer (Windows)

### Debug Commands
```bash
# Check bot status
ps aux | grep python

# Check temp directory
ls -la /tmp/discord_bot_audio/

# Check disk usage
du -sh /tmp/discord_bot_audio/

# Monitor real-time logs
tail -f bot.log
```

### Emergency Procedures
1. **Stop bot**: `Ctrl+C` or `docker-compose down`
2. **Clear temp files**: `rm -rf /tmp/discord_bot_audio/*`
3. **Restart bot**: `python bot.py` or `docker-compose up -d`
4. **Check logs**: Review for error patterns
5. **Restore backup**: If needed, restore from backup

---

*Integration Checklist v2.1.0 - Ready for Production Deployment*
