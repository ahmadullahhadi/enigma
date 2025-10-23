# 🎵 Discord Music Bot

A production-ready Discord music bot built with Python 3.11+, discord.py 2.x, and yt-dlp. Features slash commands, interactive controls, queue management, and Docker deployment.

## ✨ Features

- **Slash Commands Only** - Modern Discord app commands interface
- **YouTube Support** - Play from URLs or search terms using yt-dlp
- **Download-First Playback** - Stable audio playback with download-before-play system
- **Real-Time Embed Updates** - Live progress bars, time tracking, and dynamic playback state
- **Comprehensive Admin Logging** - All voice, playback, and error events logged privately to admin channel
- **Persistent Control Panel** - Music controls automatically reposition to stay at channel bottom
- **Minimalist Design** - All feedback integrated into existing embed, zero public message clutter
- **Dynamic Channel Status** - Voice channel status updates to show currently playing tracks
- **Accurate Queue Counter** - Shows session position and real queue length dynamically
- **Premium Playlist System** - Instant playback, smart preloading, zero progress spam, 6 dedicated commands
- **Dual Playback Modes** - Choose between download-first (stable) or streaming (fast) modes
- **Queue Management** - Per-guild queues with shuffle, loop, and skip controls
- **Paginated Queue Display** - Navigate through large queues with Previous/Next buttons
- **Interactive Controls** - Button-based playback controls on now-playing embeds
- **Loop Modes** - Loop single tracks or entire queues
- **Volume Control** - Adjustable playback volume per server
- **Multi-Server Optimized** - Isolated per-guild states, auto-cleanup, concurrent playback
- **Robust Error Handling** - Graceful failures with auto-skip and clear user feedback
- **Docker Ready** - Full containerization with docker-compose support
- **Production Grade** - Memory efficient, fault tolerant, scales to hundreds of servers

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/play <query>` | Play a song/playlist from YouTube URL or search term |
| `/join` | Join your current voice channel |
| `/pause` | Pause the current track |
| `/resume` | Resume playback |
| `/skip` | Skip to the next track |
| `/queue` | Show the current queue with pagination |
| `/shuffle` | Shuffle the queue |
| `/loop <mode>` | Set loop mode (off/track/queue) |
| `/stop` | Stop playback and clear queue |
| `/now` | Show currently playing track with detailed info |
| `/volume <level>` | Set playback volume (0-100) |
| `/remove <position>` | Remove a specific track from queue |
| `/clear` | Clear the entire queue |
| `/leave` | Disconnect from voice channel |

## 🎮 Interactive Controls

Each now-playing message includes interactive buttons:

- ⏯️ **Pause/Resume** - Toggle playback
- ⏭️ **Skip** - Skip to next track
- 🔁 **Loop** - Cycle through loop modes
- 🔀 **Shuffle** - Shuffle the queue
- ⏹️ **Stop** - Stop and clear queue
- ➕ **Add Song** - Quick add songs via popup modal
- 📜 **Queue** - View current queue with pagination
- ❌ **Leave** - Disconnect from voice

## 🎯 Download-First Playback System

**NEW**: This bot now features a revolutionary download-first playback system that eliminates common audio issues:

### Problems Solved
- ❌ **Random playback speed increases** - No more chipmunk voices!
- ❌ **Audio cuts and skips** - Smooth, uninterrupted playback
- ❌ **Buffering issues** - Local files play instantly
- ❌ **Network instability** - Downloaded files are immune to connection drops

### How It Works
1. **Download Phase**: When you request a song, the bot downloads the audio file to temporary storage
2. **Playback Phase**: The bot plays directly from the local file for maximum stability
3. **Cleanup Phase**: After playback, the temporary file is automatically deleted

### Configuration
Control both features via environment variables:

```env
# Enable download-first mode (recommended for stability)
DOWNLOAD_FIRST_MODE=true

# Enable dynamic channel status updates
CHANNEL_NAME_UPDATES=true

# Disable for streaming mode (faster startup, less stable)
DOWNLOAD_FIRST_MODE=false

# Disable channel status updates if not desired
CHANNEL_NAME_UPDATES=false
```

### Storage Requirements
- **Temporary Space**: ~5-15MB per song during playback
- **Auto-Cleanup**: Files are deleted immediately after each song
- **Location**: `/tmp/discord_bot_audio` (Linux/Docker) or system temp directory

## 🏷️ Dynamic Voice Channel Status

**NEW**: The bot now automatically updates voice channel status to show what's currently playing!

### How It Works
- **During Playback**: Channel status shows `🎵 Now Playing: Song Title`
- **When Stopped**: Channel status is cleared
- **Your channel name stays the same** - Only the status changes!
- **Rate Limited**: Built-in cooldown prevents Discord API rate limits

### Requirements
- Bot needs **"Manage Channels"** permission in voice channels
- Works with any voice channel the bot joins
- Automatically disabled if permissions are insufficient

### Configuration
```env
# Enable dynamic channel status updates (default: true)
CHANNEL_NAME_UPDATES=true

# Disable if you don't want this feature
CHANNEL_NAME_UPDATES=false
```

### Features
- **Non-Intrusive**: Your channel name remains unchanged
- **Automatic Clearing**: Status is cleared when playback stops
- **Length Limiting**: Truncates long titles to fit Discord's 500-char limit
- **Cooldown Protection**: Prevents rate limit issues with 5-second cooldowns
- **Error Handling**: Gracefully handles permission issues

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- FFmpeg installed on your system

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd discord-music-bot
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Edit .env and add your bot token**
   ```env
   BOT_TOKEN=your_actual_bot_token_here
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

### Docker Setup (Recommended)

1. **Create .env file**
   ```bash
   cp .env.example .env
   # Edit .env with your bot token
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f music-bot
   ```

4. **Stop the bot**
   ```bash
   docker-compose down
   ```

### Manual Docker Build

```bash
# Build the image
docker build -t discord-music-bot .

# Run the container
docker run -d --name music-bot --env-file .env discord-music-bot

# View logs
docker logs -f music-bot
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ Yes | - | Your Discord bot token |
| `GUILD_ID` | ❌ No | - | Guild ID for faster dev command sync |
| `OWNER_ID` | ❌ No | - | Bot owner's Discord user ID |
| `FFMPEG_PATH` | ❌ No | `ffmpeg` | Path to ffmpeg executable |
| `QUEUE_TIMEOUT` | ❌ No | `300` | Idle timeout in seconds before disconnect |

### Bot Permissions

Your bot needs the following permissions:

- **Read Messages/View Channels** - To see commands
- **Send Messages** - To send embeds and responses
- **Connect** - To join voice channels
- **Speak** - To play audio
- **Use Slash Commands** - To register commands

**Permission Integer**: `3165184` (or use the link generator in Discord Developer Portal)

### Inviting the Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to OAuth2 → URL Generator
4. Select scopes: `bot` and `applications.commands`
5. Select permissions listed above
6. Use the generated URL to invite the bot

## 🔧 Troubleshooting

### Commands Not Showing Up

- If you set `GUILD_ID` in `.env`, commands sync instantly to that guild
- Without `GUILD_ID`, global sync takes **up to 1 hour**
- Try kicking and re-inviting the bot with the correct permissions
- Ensure `applications.commands` scope was selected during invite

### FFmpeg Not Found

**Linux/Docker**: Already installed in the Dockerfile

**Windows**:
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract and add to PATH, or set `FFMPEG_PATH` in `.env`:
   ```env
   FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
   ```

**macOS**:
```bash
brew install ffmpeg
```

### Voice Connection Issues

- Ensure bot has **Connect** and **Speak** permissions
- Check if you're in a voice channel when using `/play`
- Verify `PyNaCl` is installed: `pip install PyNaCl`

### yt-dlp Extraction Errors

- Update yt-dlp: `pip install --upgrade yt-dlp`
- Some videos may be region-locked or age-restricted
- Try a different video or search query

### YouTube "Sign in to confirm you're not a bot" Error

YouTube now requires cookies for authentication. **See [YOUTUBE_COOKIES_GUIDE.md](YOUTUBE_COOKIES_GUIDE.md) for detailed setup instructions.**

**Quick Fix:**
1. Install browser extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Login to YouTube in your browser
3. Export cookies to `cookies.txt` in bot directory
4. Restart bot: `docker-compose restart` (or `python bot.py`)

The bot will automatically use cookies from `./cookies.txt` if present.

### Bot Not Responding

- Check bot is online in Discord
- View logs: `docker-compose logs -f` or check console output
- Verify bot token is correct in `.env`
- Ensure intents are enabled in Developer Portal

## 📁 Project Structure

```
discord-music-bot/
├── bot.py                 # Main entry point
├── cogs/
│   ├── __init__.py
│   └── music.py          # Music cog with commands
├── utils/
│   ├── __init__.py
│   └── yt.py             # YouTube/yt-dlp utilities
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── .env.example          # Environment variables template
├── README.md             # This file
└── LICENSE               # MIT License
```

## 🔐 Security Best Practices

- **Never commit `.env`** - Add it to `.gitignore`
- **Use environment variables** - Don't hardcode tokens
- **Run as non-root** - Dockerfile uses unprivileged user
- **Keep dependencies updated** - Regularly update packages
- **Limit bot permissions** - Only grant necessary permissions

## 🐳 Production Deployment

### systemd Service (Linux)

Create `/etc/systemd/system/discord-music-bot.service`:

```ini
[Unit]
Description=Discord Music Bot
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/path/to/discord-music-bot
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable discord-music-bot
sudo systemctl start discord-music-bot
```

### Docker Swarm / Kubernetes

The bot is stateless and can be deployed to orchestration platforms. Ensure:
- Environment variables are injected via secrets/configmaps
- Persistent volume for cache (optional)
- Health checks are configured

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube extractor
- [FFmpeg](https://ffmpeg.org/) - Audio processing

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the logs: `docker-compose logs -f`
3. Open an issue on GitHub with detailed error messages

---

Made with ❤️ for the Discord community
