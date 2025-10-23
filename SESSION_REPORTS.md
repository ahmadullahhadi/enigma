# 📊 Session Reports Feature

## Overview

The Discord Music Bot now automatically tracks every listening session and generates comprehensive reports when the bot leaves the voice channel. These reports provide detailed statistics about what was played, who requested tracks, and how long the session lasted.

---

## ✨ What Gets Tracked

### **Automatic Session Tracking** 📝
- **All Tracks Played**: Complete list of every song played during the session
- **Requesters**: Who requested each track
- **Durations**: Individual track durations and total listened time
- **Session Timeline**: Start time and total session duration
- **Play Order**: Chronological order of tracks played

### **Session Start Conditions**
Session tracking automatically starts when:
- ✅ First track starts playing after bot joins
- ✅ First track plays after previous session ended
- ✅ Bot rejoins voice channel

### **Session End Conditions**
Session tracking ends and report is sent when:
- ✅ Bot is kicked/disconnected from voice
- ✅ Bot leaves voice channel (Leave button or command)
- ✅ Bot stops playback (Stop button)
- ✅ Bot auto-disconnects due to inactivity
- ✅ Bot goes offline or restarts
- ✅ Guild cleanup triggered

---

## 📊 Session Report Structure

### **Main Report Embed**
```
📊 Session Report
━━━━━━━━━━━━━━━━━━━━
🎵 **Music session ended - [Reason]**

📝 Summary of your listening session

🕒 Session Duration     🎶 Total Listened     📀 Tracks Played
`45:30`                 `42:15`               `12`

🎵 Recently Played
`1.` **Song Title One**
⏱️ 3:45 • 👤 Username1

`2.` **Song Title Two**
⏱️ 4:20 • 👤 Username2

... (up to 10 most recent tracks shown)

*...and 2 more tracks*
━━━━━━━━━━━━━━━━━━━━
Session ended at 23:45:30
```

### **Disconnect Reasons** 🔍
- **"Bot disconnected from voice"** - Kicked or moved
- **"Bot left voice channel"** - User pressed Leave button
- **"Playback stopped"** - User pressed Stop button
- **"Auto-disconnect due to inactivity"** - Idle timeout
- **"Bot cleanup"** - Bot shutdown or restart

---

## 🎮 Interactive Features

### **View Full Session Details Button** 📊

Every session report includes a button to view complete details:

#### Button Features:
- **Label**: "View Full Session Details"
- **Emoji**: 📊
- **Timeout**: 5 minutes
- **Ephemeral**: Yes (only visible to user who clicks)

#### Full Details View Shows:
```
📊 Full Session Report
━━━━━━━━━━━━━━━━━━━━
🎵 **Complete list of all tracks played**

Total: 25 tracks

🕒 Session Duration: `1:15:30`
🎶 Total Listened: `1:10:45`
📀 Total Tracks: `25`

🎵 All Tracks Played
`1.` **First Song Title**
   ⏱️ 3:45 • 👤 Username1

`2.` **Second Song Title**
   ⏱️ 4:20 • 👤 Username2

... (all tracks listed)

`25.` **Last Song Title**
   ⏱️ 2:50 • 👤 Username5
```

### **Handling Long Sessions** 📜

For sessions with many tracks (>25):
- **Summary View**: Shows last 10 tracks
- **Full Details**: Shows first 20 and last 5
- **Indication**: "*...middle tracks omitted...*"

---

## 🔧 Technical Implementation

### **Data Structure**

#### **Session Tracking**
```python
# GuildMusicState attributes
session_start_time: float          # Timestamp when session started
session_tracks: List[Dict]         # List of track data
session_active: bool               # Whether session is active

# Track data structure
{
    'track': Track,                # Track object
    'requester': discord.Member,   # Who requested
    'started_at': float,           # When track started
    'duration': int,               # Track duration in seconds
    'title': str,                  # Track title
    'uploader': str,               # Channel/artist name
    'webpage_url': str            # YouTube URL
}
```

### **Key Methods**

#### **GuildMusicState Methods**
```python
start_session()
    # Initialize new session tracking

record_track_play(track: Track)
    # Record when a track starts playing

get_session_duration() -> int
    # Calculate total session time

get_total_listened_duration() -> int
    # Sum of all track durations

generate_session_report(music_cog) -> Embed
    # Create session report embed

send_session_report(music_cog, reason: str)
    # Send report to text channel

end_session()
    # Mark session as ended
```

### **Integration Points**

#### **Track Play Recording**
```python
# In _play_next after track starts playing
state.record_track_play(track)
```

#### **Session Report Triggers**
```python
# On voice disconnect
await state.send_session_report(self, "Bot disconnected...")

# On leave button
await state.send_session_report(self, "Bot left voice...")

# On stop button
await state.send_session_report(self, "Playback stopped")

# On idle disconnect
await state.send_session_report(music_cog, "Auto-disconnect...")

# On cleanup
await state.send_session_report(self, "Bot cleanup")
```

---

## 📊 Queue Counter Fix

### **Previous Issue** ❌
```
Track Position: 5 / 10
Problem: Showed cumulative count (total ever added)
After songs finished: Still showed old total
```

### **New System** ✅
```
Track Info: Session #5 • 4 in queue
Shows: Current position in session • Actual queue length
After songs finish: Accurate queue count
```

### **What Changed**
- **Removed**: `total_tracks` increment on add
- **Added**: Dynamic queue count with `len(self.queue)`
- **Display**: Session position + current queue length
- **Result**: Always accurate queue information

---

## 💡 User Experience

### **Automatic Operation** 🔄
- **No commands needed** - Completely automatic
- **Silent tracking** - No interruption during playback
- **Smart reports** - Only sent when there's activity

### **What Users See**

#### **During Session**
```
🎵 Now Playing
━━━━━━━━━━━━━━
[Progress Bar]
`2:30` / `4:00` • `-1:30` remaining

📊 Track Info
**Session #3** • `5` in queue
```
*Queue count updates in real-time as songs are added/removed*

#### **On Disconnect**
```
📊 Session Report appears automatically
- Summary of session
- Last 10 tracks
- Button to view full details
```

---

## 🎯 Benefits

### **For Users** 👥
- ✅ **Track History**: See what was played
- ✅ **Session Stats**: Know how long you listened
- ✅ **Accountability**: See who requested what
- ✅ **Memory Aid**: Remember great songs

### **For Server Admins** 👨‍💼
- ✅ **Usage Tracking**: Monitor bot usage
- ✅ **User Activity**: See who's active
- ✅ **Problem Detection**: Identify disconnect patterns
- ✅ **Statistics**: Overall listening trends

---

## 🛡️ Error Handling

### **Graceful Degradation**
```python
# No tracks played
if not session_tracks:
    return  # No report sent

# No text channel
if not text_channel:
    return  # Can't send report

# Error sending report
except Exception as e:
    print(f"Error: {e}")
    # Session still ends, no user interruption
```

### **Edge Cases Handled**
- ✅ Empty sessions (no tracks played)
- ✅ Missing text channel reference
- ✅ Permission errors sending embeds
- ✅ Very long track lists (truncation)
- ✅ Multiple rapid disconnects
- ✅ Bot restart during session

---

## 📈 Performance Impact

### **Memory Usage**
- **Per Track**: ~1KB (metadata only, no audio)
- **100 Track Session**: ~100KB memory
- **Cleared**: On session end
- **Impact**: Negligible

### **API Calls**
- **On Disconnect**: 1 message send
- **Button Click**: 1 ephemeral response
- **Total**: Minimal API usage

### **Storage**
- **No persistence**: Data not saved to disk
- **In-memory only**: Cleared on session end
- **No database**: No long-term storage

---

## 🔮 Future Enhancements

### **Potential Features**
- **Export to CSV**: Download session data as file
- **Statistics Charts**: Visual graphs of listening habits
- **Top Tracks**: Most played songs over time
- **User Leaderboards**: Who requests most songs
- **Playlist Generation**: Create playlist from session
- **Session Comparison**: Compare multiple sessions
- **Persistent Storage**: Save history across restarts

---

## 📝 Example Session Flow

### **Complete Session Example**

```
1. User: /play never gonna give you up
   → Session starts
   → Track #1 recorded

2. User: /play bohemian rhapsody
   → Track #2 recorded

3. Song 1 finishes → Song 2 starts playing
   → Track #2 updates with actual play time

4. User adds 5 more songs
   → Tracks #3-#7 recorded

5. User presses Leave button
   → Session ends
   → Report generated and sent
   → Shows: 7 tracks, session duration, etc.
   → Button to view full details available
```

---

## 🎯 Summary

### ✅ What This Feature Provides
- **Complete session tracking** from first to last song
- **Automatic reports** on all disconnect scenarios
- **Interactive details** via button click
- **Accurate queue counting** at all times
- **Zero user interaction** required

### ✅ Key Benefits
- Transparent music activity tracking
- Historical record of listening sessions
- Easy troubleshooting of disconnects
- Enhanced user experience
- Valuable usage statistics

### ✅ Technical Quality
- Minimal memory footprint
- No database requirements
- Comprehensive error handling
- Clean code integration
- Zero breaking changes

---

*Session Reports v1.0 - Track Everything, Miss Nothing* 📊
