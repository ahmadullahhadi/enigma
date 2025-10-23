# 🍪 YouTube Cookies Setup Guide

## Why Do I Need This?

YouTube now requires authentication to prevent bot access. Your Discord music bot needs cookies from an authenticated browser session to bypass this restriction.

## Error You're Seeing

```
ERROR: [youtube] Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies for the authentication.
```

## Quick Solution Overview

You need to:
1. Install a browser extension to export cookies
2. Log into YouTube in your browser
3. Export cookies to a file named `cookies.txt`
4. Place it in your bot's directory
5. Restart the bot

---

## 📋 Method 1: Using Browser Extension (Easiest)

### For Chrome/Edge/Brave

1. **Install the Extension**
   - Go to: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Click "Add to Chrome/Edge/Brave"

2. **Login to YouTube**
   - Open https://youtube.com in your browser
   - Sign in with your Google account
   - Watch any video to confirm your session is active

3. **Export Cookies**
   - Click the "Get cookies.txt LOCALLY" extension icon in your browser
   - Click "Export" or "Copy"
   - Save the file as `cookies.txt` in your bot directory

4. **Verify File Location**
   ```
   discord-music-bot/
   ├── cookies.txt          ← File should be here
   ├── bot.py
   ├── docker-compose.yml
   └── ...
   ```

### For Firefox

1. **Install the Extension**
   - Go to: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
   - Click "Add to Firefox"

2. **Login to YouTube**
   - Open https://youtube.com
   - Sign in with your account

3. **Export Cookies**
   - Click the extension icon
   - Select "Current Site" 
   - Click "Export" and save as `cookies.txt` in your bot directory

---

## 📋 Method 2: Using yt-dlp Command (Advanced)

If you have Chrome installed, yt-dlp can extract cookies automatically:

```bash
# Extract cookies from Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Note:** Make sure Chrome is closed when running this command.

For other browsers:
- Firefox: `--cookies-from-browser firefox`
- Edge: `--cookies-from-browser edge`
- Safari: `--cookies-from-browser safari`

---

## 🐳 For Docker Users

### Step 1: Create cookies.txt

Follow Method 1 or Method 2 above to create `cookies.txt` in your bot directory.

### Step 2: Verify Docker Mount

The `docker-compose.yml` should already have this line:

```yaml
volumes:
  - ./cookies.txt:/app/cookies.txt:ro  # YouTube cookies
```

### Step 3: Restart Container

```bash
docker-compose down
docker-compose up -d
```

---

## 🔧 For Local Python Setup

### Step 1: Create cookies.txt

Follow Method 1 or Method 2 to create `cookies.txt`.

### Step 2: Set Environment Variable (Optional)

If you want to use a custom path, add to your `.env`:

```env
YT_COOKIES_PATH=/path/to/your/cookies.txt
```

Otherwise, the bot will automatically look for `./cookies.txt` in the bot directory.

### Step 3: Restart Bot

```bash
python bot.py
```

---

## ✅ Verification

After setup, try playing a song:

```
/play never gonna give you up
```

If you still get cookie errors:

1. **Check File Exists**
   ```bash
   # Windows
   dir cookies.txt
   
   # Linux/Mac
   ls -la cookies.txt
   ```

2. **Check File Format**
   - Open `cookies.txt` in a text editor
   - First line should be: `# Netscape HTTP Cookie File`
   - Should contain lines with YouTube cookies

3. **Try Fresh Cookies**
   - Clear your browser cache
   - Log out and back into YouTube
   - Re-export cookies

---

## 🔒 Security Notes

⚠️ **Important:** Your `cookies.txt` file contains your YouTube session!

- **Never commit `cookies.txt` to Git** - It's already in `.gitignore`
- **Don't share this file** - Anyone with it can access your YouTube account
- **Regenerate periodically** - Cookies expire after a few months
- **Use a dedicated account** - Consider using a separate Google account for the bot

---

## ⏰ Cookie Expiration

YouTube cookies typically last **2-3 months**. If you start getting authentication errors again:

1. Re-export fresh cookies from your browser
2. Replace the old `cookies.txt` file
3. Restart the bot

---

## 🐛 Troubleshooting

### "No such file or directory: cookies.txt"

**Solution:** Make sure `cookies.txt` is in the same directory as `bot.py` and `docker-compose.yml`.

```bash
# Check current directory
pwd  # Linux/Mac
cd   # Windows

# List files
ls   # Linux/Mac
dir  # Windows
```

### "Invalid cookie file"

**Solution:** The cookie format might be wrong. Try:

1. Use a different browser extension
2. Make sure you're logged into YouTube before exporting
3. Check that the file starts with `# Netscape HTTP Cookie File`

### Bot still can't play songs

**Solution:**

1. **Update yt-dlp:**
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **Test cookies manually:**
   ```bash
   yt-dlp --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
   ```

3. **Check bot logs:**
   ```bash
   docker-compose logs -f music-bot
   ```

### "Access denied" or "Private video"

**Solution:** The account you used for cookies might not have access. Try:

1. Make sure you're logged into YouTube before exporting cookies
2. Test playing a public video first
3. Check that the account has appropriate permissions

---

## 🔄 Alternative: Use Spotify/SoundCloud

If YouTube continues to be problematic, consider:

- **Spotify:** Requires API credentials but more stable
- **SoundCloud:** Generally doesn't require cookies
- **Direct MP3 URLs:** Always work without authentication

---

## 📚 Additional Resources

- **yt-dlp FAQ:** https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp
- **Cookie Export Guide:** https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies
- **yt-dlp Documentation:** https://github.com/yt-dlp/yt-dlp

---

## 💡 Quick Reference

**File Location:**
```
./cookies.txt
```

**File Format:**
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	...	[cookie data]
```

**Docker Restart:**
```bash
docker-compose restart
```

**Test Command:**
```bash
yt-dlp --cookies cookies.txt "https://youtube.com/watch?v=test"
```

---

Made with ❤️ for the Discord community
