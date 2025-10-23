# Changelog

All notable changes to this Discord Music Bot will be documented in this file.

## [2.1.0] - 2024-10-10 - Dynamic Voice Channel Names

### 🏷️ Major Features Added

#### Dynamic Voice Channel Name Updates
- **Real-time channel updates**: Voice channel names automatically update to show currently playing tracks
- **Smart sanitization**: Handles special characters and long titles safely
- **Automatic restoration**: Original channel names are always restored when playback stops
- **Rate limit protection**: Built-in cooldown system prevents Discord API rate limits
- **Permission handling**: Gracefully handles insufficient permissions and auto-disables if needed
- **Configurable**: Toggle via `CHANNEL_NAME_UPDATES` environment variable

### 🔧 Technical Improvements

#### New VoiceChannelManager Class
- **Channel name tracking**: Stores original names for proper restoration
- **Cooldown management**: 10-second cooldown between renames to avoid rate limits
- **Safe sanitization**: Removes problematic characters (`<>:"/\\|?*`) from track names
- **Length limiting**: Truncates long titles to fit Discord's 100-character limit
- **Error handling**: Comprehensive error handling for permissions and API issues

#### Enhanced GuildMusicState
- **Integrated channel management**: Each guild state has its own VoiceChannelManager
- **Automatic updates**: Channel names update on play/stop/pause/skip events
- **Cleanup integration**: Channel names restored during all cleanup operations

### 🎮 User Experience

#### Visual Feedback
- **Playing indicator**: Channel shows `🎵 Song Title` during playback
- **Original restoration**: Channel reverts to original name when stopped
- **Seamless integration**: Works with all existing bot commands and features

---

## [2.0.0] - 2024-10-09 - Download-First Playback System

### 🎯 Major Features Added

#### Download-First Playback System
- **Revolutionary playback stability**: Implemented download-before-play system to eliminate audio issues
- **Automatic fallback**: Falls back to streaming mode if download fails
- **Configurable modes**: Toggle between download-first and streaming via `DOWNLOAD_FIRST_MODE` environment variable
- **Smart temporary storage**: Uses system temp directory with automatic cleanup

### 🐛 Issues Fixed

#### Audio Playback Issues
- ✅ **Fixed random playback speed increases** - No more "chipmunk voice" effect
- ✅ **Eliminated audio cuts and skips** - Smooth, uninterrupted playback from local files
- ✅ **Resolved buffering problems** - Local files play instantly without network delays
- ✅ **Improved network stability** - Downloaded files immune to connection drops

### 🔧 Technical Improvements

#### Enhanced YTDLSource Class (`utils/yt.py`)
- Added `download_track()` method for downloading audio files
- Added `cleanup_track_file()` for proper file cleanup
- Added `cleanup_all_temp_files()` for shutdown cleanup
- New `YTDL_DOWNLOAD_OPTIONS` configuration for download mode
- Improved error handling and fallback mechanisms

#### Updated Track Class (`cogs/music.py`)
- Added `local_file` property for downloaded file path
- Added `temp_dir` property for cleanup management
- Added `is_downloaded` flag to track playback mode
- Added `get_audio_source()` method to return appropriate audio source
- Added `cleanup()` method for file cleanup

#### Enhanced Music Cog
- Modified `_play_next()` to support both local files and streaming
- Updated `_handle_single_track()` with download-first logic
- Added comprehensive cleanup in `cog_unload()` and `cleanup_state()`
- Added download status indicators in embed messages
- Improved FFmpeg options for local file playback

#### Bot Lifecycle Management
- Enhanced shutdown process in `bot.py` with proper cleanup
- Added cleanup calls in signal handlers
- Improved error handling during shutdown

### 📦 Dependencies

#### New Dependencies
- `ffmpeg-python>=0.2.0` - Enhanced FFmpeg integration

#### Updated Dependencies
- All existing dependencies maintained for backward compatibility

### ⚙️ Configuration

#### New Environment Variables
```env
# Download-first playback mode (default: true)
DOWNLOAD_FIRST_MODE=true

# Voice channel name updates (default: true)
CHANNEL_NAME_UPDATES=true
```

#### Updated .env.example
- Added comprehensive documentation for new download-first mode
- Included storage requirements and configuration options

### 🔄 Migration Guide

#### For Existing Users
1. **No breaking changes** - Bot works with existing configurations
2. **Optional upgrade** - Download-first mode enabled by default
3. **Fallback protection** - Automatically falls back to streaming if needed

#### For New Users
1. **Recommended setup** - Use download-first mode for best experience
2. **Storage consideration** - Ensure adequate temporary storage space
3. **Network optimization** - Download-first reduces bandwidth during playback

### 📊 Performance Impact

#### Storage
- **Temporary usage**: ~5-15MB per song during playback
- **Cleanup**: Automatic deletion after each song
- **Location**: System temp directory (`/tmp/discord_bot_audio` on Linux)

#### Network
- **Download phase**: Higher initial bandwidth usage
- **Playback phase**: Zero network usage (local file)
- **Overall**: More predictable bandwidth patterns

#### CPU/Memory
- **Minimal impact**: Efficient temporary file management
- **Auto-cleanup**: Prevents storage accumulation
- **Optimized**: Concurrent downloads and playback

### 🛡️ Reliability Improvements

#### Error Handling
- **Graceful degradation**: Falls back to streaming on download failure
- **Comprehensive cleanup**: Prevents orphaned temporary files
- **Better logging**: Detailed status information for troubleshooting

#### Stability
- **Eliminated speed variations**: Consistent playback from local files
- **Reduced network dependencies**: Local playback immune to connection issues
- **Improved user experience**: Smoother, more reliable audio playback

### 📝 Bot Permissions

#### Required Permissions for Channel Names
- **"Manage Channels"**: Required in voice channels for name updates
- **Automatic detection**: Feature auto-disables if permissions are insufficient
- **Graceful degradation**: Bot continues to work normally without this permission

### 🔮 Future Enhancements

#### Planned Features
- **Custom name formats**: Configurable channel name templates
- **Channel status updates**: Use Discord's new channel status feature when available
- **Caching system**: Optional persistent caching for frequently played songs
- **Bandwidth optimization**: Smart download scheduling and compression
- **Analytics**: Playback quality metrics and monitoring

---

## [1.x.x] - Previous Versions

### Legacy Features
- Slash commands interface
- YouTube integration with yt-dlp
- Queue management and controls
- Interactive button controls
- Multi-server support
- Docker containerization

---

*For detailed technical documentation, see the README.md file.*
