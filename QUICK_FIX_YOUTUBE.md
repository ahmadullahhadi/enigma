# 🚨 QUICK FIX: YouTube Authentication Error

## Your Error
```
ERROR: [youtube] Sign in to confirm you're not a bot. 
Use --cookies-from-browser or --cookies for the authentication.
```

## ⚡ Quick Solution (5 minutes)

### Step 1: Install Browser Extension
**Chrome/Edge/Brave users:**
- Click here: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Click "Add to Chrome/Edge/Brave"

**Firefox users:**
- Click here: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
- Click "Add to Firefox"

### Step 2: Login to YouTube
1. Open https://youtube.com in your browser
2. Sign in with your Google account
3. Watch any video to confirm you're logged in

### Step 3: Export Cookies
1. Click the extension icon (cookie icon) in your browser toolbar
2. Click "Export" or "Copy to clipboard"
3. Save the file as `cookies.txt`
4. Place it in your bot directory (same folder as `bot.py`)

### Step 4: Restart Your Bot

**If using Docker:**
```bash
docker-compose restart
```

**If using Python directly:**
```bash
# Stop the bot (Ctrl+C)
# Then start again:
python bot.py
```

### Step 5: Test
Try playing a song:
```
/play never gonna give you up
```

## ✅ Done!

Your bot should now work with YouTube again.

---

## 📚 Need More Help?

See the full guide: **[YOUTUBE_COOKIES_GUIDE.md](YOUTUBE_COOKIES_GUIDE.md)**

## 🔒 Security Note

⚠️ **Never share or commit your `cookies.txt` file!**
- It's already added to `.gitignore`
- Contains your YouTube session data
- Treat it like a password

---

## 🐛 Still Not Working?

1. **Check file location:**
   ```bash
   # Make sure cookies.txt is in the right place
   ls -la cookies.txt  # Linux/Mac
   dir cookies.txt     # Windows
   ```

2. **Check file format:**
   - Open `cookies.txt` in a text editor
   - First line should be: `# Netscape HTTP Cookie File`

3. **Update yt-dlp:**
   ```bash
   pip install --upgrade yt-dlp
   ```

4. **Check bot logs:**
   ```bash
   docker-compose logs -f music-bot
   ```

---

## 🕒 How Long Do Cookies Last?

YouTube cookies typically last **2-3 months**. When they expire:
1. Re-export new cookies from your browser
2. Replace the old `cookies.txt`
3. Restart the bot

---

**Made with ❤️ to fix your music bot fast!**
