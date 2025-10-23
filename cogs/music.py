"""
Music cog for Discord bot.
Handles voice playback, queue management, and interactive controls.
"""

import asyncio
import random
import os
import re
import time
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.yt import ytdl_source, FFMPEG_OPTIONS, FFMPEG_PCM_OPTIONS, FFMPEG_LOCAL_OPTIONS, YTDLSource


class AdminLogger:
    """Handles all administrative logging for the music bot."""
    
    def __init__(self, bot):
        self.bot = bot
        # Read admin log channel ID from environment variable
        admin_channel_id = os.getenv('ADMIN_LOG_CHANNEL_ID')
        self.admin_channel_id = int(admin_channel_id) if admin_channel_id and admin_channel_id.isdigit() else None
    
    async def get_admin_channel(self) -> Optional[discord.TextChannel]:
        """Get the admin log channel."""
        if not self.admin_channel_id:
            # No admin channel configured
            return None
        
        try:
            channel = self.bot.get_channel(self.admin_channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(self.admin_channel_id)
            return channel
        except Exception as e:
            print(f"[AdminLog] Error getting admin channel {self.admin_channel_id}: {e}")
            return None
    
    async def log(self, title: str, description: str, color: discord.Color, fields: List[Dict] = None, guild: discord.Guild = None):
        """Send a log message to the admin channel."""
        try:
            channel = await self.get_admin_channel()
            if not channel:
                return
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.utcnow()
            )
            
            # Add guild information if provided
            if guild:
                embed.add_field(name="🏰 Server", value=f"{guild.name} (`{guild.id}`)", inline=False)
            
            # Add custom fields
            if fields:
                for field in fields:
                    embed.add_field(
                        name=field.get('name', 'Field'),
                        value=field.get('value', 'N/A'),
                        inline=field.get('inline', True)
                    )
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"[AdminLog] Error sending log: {e}")
    
    async def log_track_play(self, guild: discord.Guild, track, requester: discord.Member, session_position: int):
        """Log when a track starts playing."""
        fields = [
            {'name': '🎵 Track', 'value': track.title[:100], 'inline': False},
            {'name': '📺 Channel', 'value': track.uploader[:50], 'inline': True},
            {'name': '⏱️ Duration', 'value': track.duration_str, 'inline': True},
            {'name': '👤 Requested By', 'value': f"{requester.mention} ({requester.display_name})", 'inline': True},
            {'name': '📊 Session Position', 'value': f"#{session_position}", 'inline': True},
            {'name': '🔗 URL', 'value': f"[YouTube]({track.webpage_url})", 'inline': False}
        ]
        
        await self.log(
            title="▶️ Track Started",
            description="A new track has started playing",
            color=discord.Color.green(),
            fields=fields,
            guild=guild
        )
    
    async def log_track_skip(self, guild: discord.Guild, track, user: discord.Member, reason: str = "Manual skip"):
        """Log when a track is skipped."""
        fields = [
            {'name': '🎵 Skipped Track', 'value': track.title[:100], 'inline': False},
            {'name': '👤 Skipped By', 'value': f"{user.mention} ({user.display_name})", 'inline': True},
            {'name': '❓ Reason', 'value': reason, 'inline': True}
        ]
        
        await self.log(
            title="⏭️ Track Skipped",
            description="A track was skipped",
            color=discord.Color.orange(),
            fields=fields,
            guild=guild
        )
    
    async def log_playback_action(self, guild: discord.Guild, action: str, user: discord.Member, details: str = None):
        """Log playback actions (pause, resume, stop, loop, etc.)."""
        fields = [
            {'name': '🎮 Action', 'value': action, 'inline': True},
            {'name': '👤 User', 'value': f"{user.mention} ({user.display_name})", 'inline': True}
        ]
        
        if details:
            fields.append({'name': '📝 Details', 'value': details, 'inline': False})
        
        # Color based on action
        color_map = {
            'pause': discord.Color.yellow(),
            'resume': discord.Color.green(),
            'stop': discord.Color.red(),
            'loop': discord.Color.blue()
        }
        color = color_map.get(action.lower(), discord.Color.greyple())
        
        await self.log(
            title=f"🎮 Playback Action: {action.title()}",
            description="Playback state changed",
            color=color,
            fields=fields,
            guild=guild
        )
    
    async def log_queue_update(self, guild: discord.Guild, action: str, track, user: discord.Member):
        """Log queue modifications."""
        fields = [
            {'name': '📝 Action', 'value': action, 'inline': True},
            {'name': '🎵 Track', 'value': track.title[:100], 'inline': False},
            {'name': '👤 User', 'value': f"{user.mention} ({user.display_name})", 'inline': True}
        ]
        
        await self.log(
            title="📋 Queue Updated",
            description=f"Queue {action.lower()}",
            color=discord.Color.blue(),
            fields=fields,
            guild=guild
        )
    
    async def log_voice_event(self, guild: discord.Guild, event: str, channel: discord.VoiceChannel = None, user: discord.Member = None):
        """Log bot join/leave events."""
        fields = []
        
        if channel:
            fields.append({'name': '📢 Channel', 'value': f"{channel.mention} ({channel.name})", 'inline': True})
        
        if user:
            fields.append({'name': '👤 Triggered By', 'value': f"{user.mention} ({user.display_name})", 'inline': True})
        
        color_map = {
            'joined': discord.Color.green(),
            'left': discord.Color.orange(),
            'disconnected': discord.Color.red(),
            'kicked': discord.Color.dark_red()
        }
        color = color_map.get(event.lower(), discord.Color.greyple())
        
        await self.log(
            title=f"🔊 Voice Event: {event.title()}",
            description=f"Bot {event} voice channel",
            color=color,
            fields=fields,
            guild=guild
        )
    
    async def log_error(self, guild: discord.Guild, error_type: str, error_message: str, context: str = None):
        """Log errors and exceptions."""
        fields = [
            {'name': '❌ Error Type', 'value': error_type, 'inline': True},
            {'name': '📝 Message', 'value': error_message[:1000], 'inline': False}
        ]
        
        if context:
            fields.append({'name': '🔍 Context', 'value': context[:500], 'inline': False})
        
        await self.log(
            title="⚠️ Error Occurred",
            description="An error was encountered",
            color=discord.Color.red(),
            fields=fields,
            guild=guild
        )
    
    async def log_session_summary(self, guild: discord.Guild, session_tracks: List[Dict], session_duration: int, listened_duration: int, reason: str):
        """Log session summary to admin channel."""
        def format_time(seconds: int) -> str:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {secs}s"
            return f"{minutes}m {secs}s"
        
        # Build track list
        track_list = []
        for i, track_data in enumerate(session_tracks[-10:], 1):
            duration_str = format_time(track_data['duration']) if track_data['duration'] else "Unknown"
            requester_name = track_data['requester'].display_name
            title = track_data['title'][:40] + "..." if len(track_data['title']) > 40 else track_data['title']
            track_list.append(f"`{i}.` {title} - {duration_str} by {requester_name}")
        
        tracks_text = "\n".join(track_list) if track_list else "No tracks played"
        
        if len(session_tracks) > 10:
            tracks_text += f"\n\n*...and {len(session_tracks) - 10} more tracks*"
        
        fields = [
            {'name': '🕒 Session Duration', 'value': format_time(session_duration), 'inline': True},
            {'name': '🎶 Total Listened', 'value': format_time(listened_duration), 'inline': True},
            {'name': '📀 Tracks Played', 'value': str(len(session_tracks)), 'inline': True},
            {'name': '❓ End Reason', 'value': reason, 'inline': False},
            {'name': '🎵 Recent Tracks', 'value': tracks_text, 'inline': False}
        ]
        
        await self.log(
            title="📊 Session Ended",
            description="Music session has concluded",
            color=discord.Color.purple(),
            fields=fields,
            guild=guild
        )
    
    async def log_playlist_added(self, guild: discord.Guild, playlist_title: str, total_tracks: int, total_duration: int, user: discord.Member):
        """Log when a playlist is added."""
        def format_time(seconds: int) -> str:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {secs}s"
            return f"{minutes}m {secs}s"
        
        duration_str = format_time(total_duration) if total_duration > 0 else "Unknown"
        
        fields = [
            {'name': '📜 Playlist Name', 'value': playlist_title[:100], 'inline': False},
            {'name': '📊 Total Tracks', 'value': str(total_tracks), 'inline': True},
            {'name': '⏱️ Total Duration', 'value': duration_str, 'inline': True},
            {'name': '👤 Added By', 'value': f"{user.mention} ({user.display_name})", 'inline': True}
        ]
        
        await self.log(
            title="📜 Playlist Added",
            description="A playlist has been queued",
            color=discord.Color.blue(),
            fields=fields,
            guild=guild
        )
    
    async def log_playlist_complete(self, guild: discord.Guild, playlist_title: str, tracks_played: int, user: discord.Member):
        """Log when a playlist finishes playing."""
        fields = [
            {'name': '📜 Playlist', 'value': playlist_title[:100], 'inline': False},
            {'name': '✅ Tracks Played', 'value': str(tracks_played), 'inline': True},
            {'name': '👤 Added By', 'value': f"{user.mention} ({user.display_name})", 'inline': True}
        ]
        
        await self.log(
            title="✅ Playlist Completed",
            description="Playlist has finished playing",
            color=discord.Color.green(),
            fields=fields,
            guild=guild
        )
    
    async def log_playlist_stopped(self, guild: discord.Guild, playlist_title: str, tracks_remaining: int, user: discord.Member, reason: str = None):
        """Log when a playlist is manually stopped."""
        fields = [
            {'name': '📜 Playlist', 'value': playlist_title[:100], 'inline': False},
            {'name': '🔢 Tracks Remaining', 'value': str(tracks_remaining), 'inline': True},
            {'name': '👤 Stopped By', 'value': f"{user.mention} ({user.display_name})", 'inline': True}
        ]
        
        if reason:
            fields.append({'name': '📝 Reason', 'value': reason, 'inline': False})
        
        await self.log(
            title="⏹️ Playlist Stopped",
            description="Playlist was manually stopped",
            color=discord.Color.orange(),
            fields=fields,
            guild=guild
        )


class LoopMode(Enum):
    OFF = 0
    TRACK = 1
    QUEUE = 2


class VoiceChannelManager:
    """Manages voice channel status updates to show currently playing tracks."""
    
    def __init__(self):
        self.last_update_time: Dict[int, float] = {}  # channel_id -> timestamp
        self.update_cooldown = 5.0  # 5 seconds between updates to avoid rate limits
        self.enabled = True
    
    def format_track_status(self, track: 'Track') -> str:
        """Format track info for channel status (500 char limit)."""
        # Discord voice status limit is 500 characters
        status = f"🎵 {track.title}"
        if len(status) > 500:
            status = f"🎵 {track.title[:497]}..."
        return status
    
    def can_update_status(self, channel_id: int) -> bool:
        """Check if enough time has passed since last update to avoid rate limits."""
        if not self.enabled:
            return False
        
        last_update = self.last_update_time.get(channel_id, 0)
        return time.time() - last_update >= self.update_cooldown
    
    async def update_channel_for_track(self, channel: discord.VoiceChannel, track: 'Track'):
        """Update channel status to show currently playing track."""
        if not self.can_update_status(channel.id):
            print(f"[ChannelManager] Skipping status update due to cooldown: {channel.name}")
            return
        
        try:
            # Create status message with track info
            status_message = self.format_track_status(track)
            
            # Update channel status
            await channel.edit(status=status_message)
            self.last_update_time[channel.id] = time.time()
            print(f"[ChannelManager] Updated channel status: {status_message}")
            
        except discord.Forbidden:
            print(f"[ChannelManager] No permission to update channel status: {channel.name}")
            self.enabled = False  # Disable feature if no permissions
        except discord.HTTPException as e:
            print(f"[ChannelManager] Failed to update channel status for {channel.name}: {e}")
        except Exception as e:
            print(f"[ChannelManager] Unexpected error updating channel status: {e}")
    
    async def clear_channel_status(self, channel: discord.VoiceChannel):
        """Clear the channel status."""
        if not self.enabled:
            return
        
        if not self.can_update_status(channel.id):
            print(f"[ChannelManager] Skipping status clear due to cooldown: {channel.name}")
            return
        
        try:
            # Clear status by setting it to None
            await channel.edit(status=None)
            self.last_update_time[channel.id] = time.time()
            print(f"[ChannelManager] Cleared channel status for: {channel.name}")
            
        except discord.Forbidden:
            print(f"[ChannelManager] No permission to clear channel status: {channel.name}")
        except discord.HTTPException as e:
            print(f"[ChannelManager] Failed to clear channel status for {channel.name}: {e}")
        except Exception as e:
            print(f"[ChannelManager] Unexpected error clearing channel status: {e}")
    
    def cleanup_channel(self, channel_id: int):
        """Clean up stored data for a channel."""
        self.last_update_time.pop(channel_id, None)
    
    def cleanup_all(self):
        """Clean up all stored data."""
        self.last_update_time.clear()


class Track:
    def __init__(self, info: Dict[str, Any], requester: discord.Member):
        self.title = info['title']
        self.url = info['url']
        self.stream_url = info['url']
        self.duration = info['duration']
        self.thumbnail = info.get('thumbnail')
        self.webpage_url = info['webpage_url']
        self.uploader = info.get('uploader', 'Unknown')
        self.requester = requester
        
        # Download-first playback support
        self.local_file = info.get('local_file')  # Path to downloaded file
        self.temp_dir = info.get('temp_dir')  # Temp directory for cleanup
        self.is_downloaded = info.get('is_downloaded', False)
    
    def get_audio_source(self) -> str:
        """Get the audio source path - local file if downloaded, stream URL otherwise."""
        if self.is_downloaded and self.local_file:
            return self.local_file
        return self.stream_url
    
    def cleanup(self):
        """Clean up downloaded files if this track was downloaded."""
        if self.is_downloaded and hasattr(self, '_ytdl_source'):
            self._ytdl_source.cleanup_track_file({
                'is_downloaded': self.is_downloaded,
                'temp_dir': self.temp_dir
            })
    
    def __str__(self):
        return f"**{self.title}** by {self.uploader}"
    
    @property
    def duration_str(self) -> str:
        return YTDLSource.format_duration(self.duration)


class GuildMusicState:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue: List[Track] = []
        self.current: Optional[Track] = None
        self.previous: Optional[Track] = None
        self.history: List[Track] = []
        self.voice_client: Optional[discord.VoiceClient] = None
        self.now_playing_message: Optional[discord.Message] = None
        self.text_channel: Optional[discord.TextChannel] = None
        
        self.loop_mode = LoopMode.OFF
        self.is_playing = False
        self.volume = 0.5
        self.current_position = 0
        self.total_tracks = 0
        self.lock = asyncio.Lock()
        
        # Session tracking for reports
        self.session_start_time: Optional[float] = None
        self.session_tracks: List[Dict] = []  # List of {track, requester, started_at, duration}
        self.session_active = False
        
        self.skip_votes: set = set()
        self.skip_threshold = 0.5
        self.disconnect_reason: Optional[str] = None
        
        self.idle_timeout = int(os.getenv('QUEUE_TIMEOUT', '300'))
        self.idle_task: Optional[asyncio.Task] = None
        
        # Voice channel name management
        self.channel_manager = VoiceChannelManager()
        self.channel_name_updates_enabled = os.getenv('CHANNEL_NAME_UPDATES', 'true').lower() == 'true'
        
        # Control panel management
        self.last_panel_move_time = 0.0  # Track when we last moved the panel
        self.panel_move_cooldown = 3.0  # 3 seconds cooldown between panel moves
        
        # Real-time embed updates
        self.embed_update_task: Optional[asyncio.Task] = None
        self.embed_update_interval = 5.0  # Update embed every 5 seconds
        self.track_start_time: Optional[float] = None  # Track when current song started
        
        # Playlist tracking
        self.current_playlist: Optional[Dict] = None  # {'title': str, 'total': int, 'added_by': Member, 'added_at': float, 'duration': int}
        self.playlist_track_index = 0  # Current track index in playlist
        self.playlist_finished = False  # Flag for playlist completion logging
    
    async def add_track(self, track: Track):
        async with self.lock:
            self.queue.append(track)
        # Update embed when track is added
        await self.update_embed_now()
    
    async def next_track(self) -> Optional[Track]:
        async with self.lock:
            if self.loop_mode == LoopMode.TRACK and self.current:
                self.skip_votes.clear()
                return self.current
            
            if self.current and self.loop_mode != LoopMode.TRACK:
                self.previous = self.current
                self.history.append(self.current)
                if len(self.history) > 50:
                    self.history.pop(0)
            
            if len(self.queue) > 0:
                self.current = self.queue.pop(0)
                self.current_position += 1
                self.skip_votes.clear()
                
                # Increment playlist index if we're in a playlist
                if self.current_playlist:
                    self.playlist_track_index += 1
                
                if self.loop_mode == LoopMode.QUEUE and self.current:
                    self.queue.append(self.current)
                
                return self.current
            
            # Playlist finished - will be logged by _play_next
            if self.current_playlist:
                self.playlist_finished = True  # Flag for logging
                self.current_playlist = None
                self.playlist_track_index = 0
            
            self.current = None
            return None
    
    async def skip(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
    
    async def clear_queue(self):
        async with self.lock:
            self.queue.clear()
        # Update embed when queue changes
        await self.update_embed_now()
    
    async def shuffle_queue(self):
        async with self.lock:
            random.shuffle(self.queue)
    
    def start_session(self):
        """Start a new listening session."""
        import time
        self.session_start_time = time.time()
        self.session_tracks = []
        self.session_active = True
        self.current_position = 0
        print(f"[Session] Started new session")
    
    def record_track_play(self, track: Track):
        """Record that a track started playing."""
        import time
        if not self.session_active:
            self.start_session()
        
        track_data = {
            'track': track,
            'requester': track.requester,
            'started_at': time.time(),
            'duration': track.duration if track.duration else 0,
            'title': track.title,
            'uploader': track.uploader,
            'webpage_url': track.webpage_url
        }
        self.session_tracks.append(track_data)
        print(f"[Session] Recorded track: {track.title}")
    
    def get_session_duration(self) -> int:
        """Get total session duration in seconds."""
        import time
        if not self.session_start_time:
            return 0
        return int(time.time() - self.session_start_time)
    
    def get_total_listened_duration(self) -> int:
        """Get total duration of all played tracks."""
        return sum(t['duration'] for t in self.session_tracks if t['duration'])
    
    async def generate_session_report(self, music_cog) -> Optional[discord.Embed]:
        """Generate a session report embed."""
        if not self.session_tracks:
            return None
        
        import time
        from datetime import datetime
        
        # Calculate stats
        total_tracks = len(self.session_tracks)
        session_duration = self.get_session_duration()
        listened_duration = self.get_total_listened_duration()
        
        # Create embed
        embed = discord.Embed(
            title="📊 Session Report",
            description=f"🎵 **Music session has ended**\n\n📝 Summary of your listening session",
            color=discord.Color.blue()
        )
        
        # Session stats
        session_time_str = self.format_time(session_duration)
        listened_time_str = self.format_time(listened_duration)
        
        embed.add_field(
            name="🕒 Session Duration",
            value=f"`{session_time_str}`",
            inline=True
        )
        embed.add_field(
            name="🎶 Total Listened",
            value=f"`{listened_time_str}`",
            inline=True
        )
        embed.add_field(
            name="📀 Tracks Played",
            value=f"`{total_tracks}`",
            inline=True
        )
        
        # List tracks (limit to 10 most recent)
        tracks_to_show = self.session_tracks[-10:] if len(self.session_tracks) > 10 else self.session_tracks
        
        track_list = []
        for i, track_data in enumerate(tracks_to_show, 1):
            duration_str = self.format_time(track_data['duration']) if track_data['duration'] else "Unknown"
            requester_name = track_data['requester'].display_name
            title = track_data['title'][:40] + "..." if len(track_data['title']) > 40 else track_data['title']
            track_list.append(f"`{i}.` **{title}**\n⏱️ {duration_str} • 👤 {requester_name}")
        
        if len(self.session_tracks) > 10:
            track_list.append(f"\n*...and {len(self.session_tracks) - 10} more tracks*")
        
        embed.add_field(
            name="🎵 Recently Played",
            value="\n".join(track_list) if track_list else "No tracks",
            inline=False
        )
        
        # Add timestamp
        embed.set_footer(text=f"Session ended at {datetime.now().strftime('%H:%M:%S')}")
        
        return embed
    
    def end_session(self):
        """End the current session."""
        self.session_active = False
        print(f"[Session] Ended session with {len(self.session_tracks)} tracks")
    
    async def send_session_report(self, music_cog, reason: str = "Session ended"):
        """Send session report to admin log channel only."""
        if not self.session_tracks:
            return
        
        try:
            # Log session summary to admin channel
            if hasattr(music_cog, 'admin_logger') and self.voice_client:
                await music_cog.admin_logger.log_session_summary(
                    self.voice_client.guild,
                    self.session_tracks,
                    self.get_session_duration(),
                    self.get_total_listened_duration(),
                    reason
                )
                print(f"[Session] Logged session to admin channel")
            
            # End session
            self.end_session()
            
        except Exception as e:
            print(f"[Session] Error logging session: {e}")
    
    async def update_channel_name_for_track(self, track: Track):
        """Update voice channel name to show currently playing track."""
        if not self.channel_name_updates_enabled or not self.voice_client:
            return
        
        try:
            channel = self.voice_client.channel
            if channel and isinstance(channel, discord.VoiceChannel):
                await self.channel_manager.update_channel_for_track(channel, track)
        except Exception as e:
            print(f"Error updating channel name: {e}")
    
    async def clear_channel_status(self):
        """Clear voice channel status."""
        if not self.channel_name_updates_enabled or not self.voice_client:
            return
        
        try:
            channel = self.voice_client.channel
            if channel and isinstance(channel, discord.VoiceChannel):
                await self.channel_manager.clear_channel_status(channel)
        except Exception as e:
            print(f"Error clearing channel status: {e}")
    
    async def cleanup_channel_manager(self):
        """Clean up channel manager data."""
        if self.voice_client and self.voice_client.channel:
            self.channel_manager.cleanup_channel(self.voice_client.channel.id)
        else:
            # Clean up all if we don't have a specific channel
            self.channel_manager.cleanup_all()
    
    def can_move_panel(self) -> bool:
        """Check if enough time has passed to move the control panel."""
        import time
        current_time = time.time()
        if current_time - self.last_panel_move_time >= self.panel_move_cooldown:
            self.last_panel_move_time = current_time
            return True
        return False
    
    def get_elapsed_time(self) -> int:
        """Get elapsed time in seconds since track started."""
        if not self.track_start_time or not self.current:
            return 0
        import time
        elapsed = int(time.time() - self.track_start_time)
        # Ensure we don't exceed track duration
        if self.current.duration:
            return min(elapsed, self.current.duration)
        return elapsed
    
    def get_remaining_time(self) -> int:
        """Get remaining time in seconds for current track."""
        if not self.current or not self.current.duration:
            return 0
        elapsed = self.get_elapsed_time()
        return max(0, self.current.duration - elapsed)
    
    def format_time(self, seconds: int) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        if seconds < 0:
            seconds = 0
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    def create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """Create a progress bar visualization."""
        filled = int(length * percentage / 100)
        bar = '█' * filled + '░' * (length - filled)
        return f"`[{bar}]`"
    
    async def update_embed_now(self):
        """Force an immediate embed update."""
        if not self.now_playing_message or not self.current:
            return
        
        try:
            # Create updated embed with current state
            embed = await self._create_now_playing_embed()
            if embed:
                await self.now_playing_message.edit(embed=embed)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            print(f"Could not update embed: {e}")
        except Exception as e:
            print(f"Unexpected error updating embed: {e}")
    
    async def _create_now_playing_embed(self) -> Optional[discord.Embed]:
        """Create the now playing embed with current playback state."""
        if not self.current:
            return None
        
        # Color scheme
        colors = [
            discord.Color.blue(), discord.Color.purple(), discord.Color.magenta(), 
            discord.Color.teal(), discord.Color.green(), discord.Color.orange(),
            discord.Color.red(), discord.Color.gold()
        ]
        color = colors[self.current_position % len(colors)]
        
        # Create embed
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{self.current.title}]({self.current.webpage_url})**\n\n🎶 *Enjoy the music!*",
            color=color
        )
        
        # Progress information
        if self.current.duration:
            elapsed = self.get_elapsed_time()
            remaining = self.get_remaining_time()
            percentage = (elapsed / self.current.duration * 100) if self.current.duration > 0 else 0
            progress_bar = self.create_progress_bar(percentage)
            
            elapsed_str = self.format_time(elapsed)
            remaining_str = self.format_time(remaining)
            total_str = self.current.duration_str
            
            progress_text = f"{progress_bar}\n`{elapsed_str}` / `{total_str}` • `-{remaining_str}` remaining"
            embed.add_field(name="⏱️ Progress", value=progress_text, inline=False)
        
        # Track info row
        embed.add_field(name="📺 Channel", value=f"`{self.current.uploader}`", inline=True)
        embed.add_field(name="👤 Requested by", value=self.current.requester.mention, inline=True)
        
        # Playback status row - show playlist position if in playlist, otherwise session position
        queue_count = len(self.queue)
        if self.current_playlist:
            # Show playlist position: "Track 5 of 300 • 295 remaining"
            position_display = f"**Track {self.playlist_track_index} of {self.current_playlist['total']}** • `{queue_count}` remaining"
            embed.add_field(name="📜 Playlist Progress", value=position_display, inline=True)
        else:
            # Show session position
            position_display = f"**Session #{self.current_position}** • `{queue_count}` in queue"
            embed.add_field(name="📊 Track Info", value=position_display, inline=True)
        
        volume_display = f"`{int(self.volume * 100)}%`"
        embed.add_field(name="🔊 Volume", value=volume_display, inline=True)
        
        # Loop mode indicator
        loop_icons = {
            LoopMode.OFF: "➡️ **Off**",
            LoopMode.TRACK: "🔂 **Track**",
            LoopMode.QUEUE: "🔁 **Queue**"
        }
        embed.add_field(name="🔁 Loop Mode", value=loop_icons[self.loop_mode], inline=True)
        
        # Playback status
        if self.voice_client:
            if self.voice_client.is_paused():
                status = "⏸️ **Paused**"
            elif self.voice_client.is_playing():
                status = "▶️ **Playing**"
            else:
                status = "⏹️ **Stopped**"
            embed.add_field(name="🎵 Status", value=status, inline=True)
        
        # Queue preview
        if len(self.queue) > 0:
            next_track = self.queue[0]
            next_title = next_track.title[:35] + "..." if len(next_track.title) > 35 else next_track.title
            next_info = f"**{next_title}**\n⏱️ `{next_track.duration_str}` • 👤 {next_track.requester.display_name}"
            embed.add_field(name="⏭️ Up Next", value=next_info, inline=False)
        else:
            embed.add_field(name="⏭️ Up Next", value="*Queue is empty - add more songs!*", inline=False)
        
        # Thumbnail
        if self.current.thumbnail:
            embed.set_thumbnail(url=self.current.thumbnail)
        
        # Footer with queue info - show playlist total when playlist is active
        queue_duration = sum(t.duration for t in self.queue if t.duration)
        queue_time_str = self.format_time(queue_duration) if queue_duration > 0 else "0:00"
        playback_mode = "📁 Downloaded" if self.current.is_downloaded else "🌐 Streaming"
        
        if self.current_playlist:
            # For playlists: Show total playlist count, not queue count
            footer_text = f"🎶 Playlist Loaded — {self.current_playlist['total']} Tracks • {queue_time_str} remaining"
        else:
            # For regular playback: Show queue count
            footer_text = f"{playback_mode} • {len(self.queue)} in queue • {queue_time_str} remaining"
        
        embed.set_footer(text=footer_text, icon_url=self.current.requester.display_avatar.url)
        
        return embed
    
    async def start_embed_updates(self, music_cog=None):
        """Start the periodic embed update task."""
        # Check if feature is enabled
        if music_cog and hasattr(music_cog, 'realtime_embed_updates'):
            if not music_cog.realtime_embed_updates:
                return  # Feature disabled
        
        if self.embed_update_task and not self.embed_update_task.done():
            return  # Already running
        
        self.embed_update_task = asyncio.create_task(self._update_embed_loop())
    
    async def stop_embed_updates(self):
        """Stop the periodic embed update task."""
        if self.embed_update_task:
            self.embed_update_task.cancel()
            try:
                await self.embed_update_task
            except asyncio.CancelledError:
                pass
            self.embed_update_task = None
    
    async def _update_embed_loop(self):
        """Background task that periodically updates the embed."""
        try:
            while self.is_playing and self.current:
                await asyncio.sleep(self.embed_update_interval)
                if self.is_playing and self.current:
                    await self.update_embed_now()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in embed update loop: {e}")
    
    async def move_panel_to_bottom(self, music_cog):
        """Move the control panel to the bottom of the channel."""
        if not self.now_playing_message or not self.current or not self.is_playing:
            return
        
        if not self.can_move_panel():
            return  # Skip if in cooldown
        
        try:
            # Get the current embed
            if not self.now_playing_message.embeds:
                return
            
            # Create fresh embed with current state
            embed = await self._create_now_playing_embed()
            if not embed:
                return
            
            channel = self.now_playing_message.channel
            
            # Delete the old message
            await self.now_playing_message.delete()
            
            # Recreate the control buttons view
            view = ControlButtons(music_cog, self.voice_client.guild.id)
            
            # Send new message at the bottom
            new_message = await channel.send(embed=embed, view=view)
            self.now_playing_message = new_message
            
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            print(f"Could not move control panel: {e}")
        except Exception as e:
            print(f"Unexpected error moving control panel: {e}")
    
    def reset_idle_timer(self):
        if self.idle_task:
            self.idle_task.cancel()
        self.idle_task = asyncio.create_task(self._idle_disconnect())
    
    async def _idle_disconnect(self):
        try:
            await asyncio.sleep(self.idle_timeout)
            if self.voice_client and not self.voice_client.is_playing():
                # Clear channel status before disconnecting
                await self.clear_channel_status()
                
                # Send session report (pass bot reference)
                if hasattr(self, 'bot'):
                    music_cog = self.bot.get_cog('Music')
                    if music_cog:
                        await self.send_session_report(music_cog, "Music session ended - Auto-disconnect due to inactivity")
                
                await self.voice_client.disconnect()
                self.voice_client = None
        except asyncio.CancelledError:
            pass


class QueuePaginator(discord.ui.View):
    def __init__(self, cog: 'Music', guild_id: int, page: int = 0):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id
        self.page = page
        self.items_per_page = 10
    
    def get_page_content(self, state: GuildMusicState) -> Tuple[discord.Embed, int]:
        # Use gradient colors for visual appeal
        colors = [discord.Color.blue(), discord.Color.purple(), discord.Color.teal(), discord.Color.green()]
        color = colors[self.page % len(colors)]
        
        embed = discord.Embed(
            title="📜 Music Queue",
            description="🎶 Your current playlist",
            color=color
        )
        
        if state.current:
            current_info = f"**[{state.current.title}]({state.current.webpage_url})**\n"
            current_info += f"⏱️ `{state.current.duration_str}` • 👤 {state.current.requester.mention}"
            embed.add_field(
                name="🎵 Now Playing",
                value=current_info,
                inline=False
            )
        
        total_tracks = len(state.queue)
        total_pages = (total_tracks + self.items_per_page - 1) // self.items_per_page if total_tracks > 0 else 1
        start_idx = self.page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_tracks)
        
        if total_tracks > 0:
            queue_text = ""
            for i in range(start_idx, end_idx):
                track = state.queue[i]
                # Better formatting with proper truncation
                title = track.title[:45] + "..." if len(track.title) > 45 else track.title
                queue_text += f"`{i+1:2d}.` **{title}**\n"
                queue_text += f"     ⏱️ `{track.duration_str}` • 👤 {track.requester.display_name}\n\n"
            
            embed.add_field(
                name=f"⏭️ Up Next • Page {self.page + 1}/{total_pages}",
                value=queue_text.strip(),
                inline=False
            )
            
            if total_tracks > end_idx:
                embed.add_field(
                    name="📊 Additional Tracks",
                    value=f"*...and {total_tracks - end_idx} more tracks waiting*",
                    inline=False
                )
        else:
            embed.add_field(
                name="⏭️ Up Next",
                value="*Queue is empty - use `/play` to add songs!*",
                inline=False
            )
        
        # Enhanced footer with more info
        loop_icons = {
            LoopMode.OFF: "➡️ No Loop",
            LoopMode.TRACK: "🔂 Loop Track",
            LoopMode.QUEUE: "🔁 Loop Queue"
        }
        
        queue_duration = sum(t.duration for t in state.queue if t.duration)
        queue_time = YTDLSource.format_duration(queue_duration) if queue_duration > 0 else "0:00"
        
        embed.set_footer(
            text=f"{loop_icons[state.loop_mode]} • {total_tracks} tracks • {queue_time} remaining"
        )
        
        return embed, total_pages
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, custom_id="queue_prev")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            state = self.cog.get_state(self.guild_id)
            embed, total_pages = self.get_page_content(state)
            
            self.previous_page.disabled = (self.page == 0)
            self.next_page.disabled = (self.page >= total_pages - 1)
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="queue_next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.cog.get_state(self.guild_id)
        total_tracks = len(state.queue)
        total_pages = (total_tracks + self.items_per_page - 1) // self.items_per_page
        
        if self.page < total_pages - 1:
            self.page += 1
            embed, total_pages = self.get_page_content(state)
            
            self.previous_page.disabled = (self.page == 0)
            self.next_page.disabled = (self.page >= total_pages - 1)
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()


class AddSongModal(discord.ui.Modal, title="Add Song to Queue"):
    song_input = discord.ui.TextInput(
        label="Song Name or URL",
        placeholder="Enter YouTube URL or search term...",
        required=True,
        max_length=200
    )
    
    def __init__(self, cog: 'Music', guild_id: int, now_playing_message: Optional[discord.Message] = None):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.now_playing_message = now_playing_message
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        query = self.song_input.value.strip()
        if not query:
            await interaction.followup.send("❌ Please enter a valid song name or URL.", ephemeral=True)
            return
        
        state = self.cog.get_state(self.guild_id)
        
        if not state.voice_client:
            await interaction.followup.send("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        await interaction.followup.send(f"🔍 Searching for: **{query}**...", ephemeral=True)
        
        # Add track and update the current embed
        await self.cog._handle_single_track(interaction, query, state, update_embed=self.now_playing_message)


class ControlButtons(discord.ui.View):
    def __init__(self, cog: 'Music', guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
    
    async def _check_permissions(self, interaction: discord.Interaction) -> bool:
        state = self.cog.get_state(self.guild_id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return False
        
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You must be in a voice channel to use controls.", ephemeral=True)
            return False
        
        if interaction.user.voice.channel != state.voice_client.channel:
            await interaction.response.send_message("❌ You must be in the same voice channel as the bot.", ephemeral=True)
            return False
        
        return True
    
    @discord.ui.button(label="Pause/Resume", emoji="⏯️", style=discord.ButtonStyle.secondary, custom_id="music_pause_resume", row=0)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permissions(interaction):
            return
        
        state = self.cog.get_state(self.guild_id)
        
        if state.voice_client.is_paused():
            state.voice_client.resume()
            await interaction.response.send_message("▶️ Resumed playback.", ephemeral=True)
            # Update embed immediately
            await state.update_embed_now()
            # Log to admin channel
            await self.cog.admin_logger.log_playback_action(
                interaction.guild, "Resume", interaction.user
            )
        elif state.voice_client.is_playing():
            state.voice_client.pause()
            await interaction.response.send_message("⏸️ Paused playback.", ephemeral=True)
            # Update embed immediately
            await state.update_embed_now()
            # Log to admin channel
            await self.cog.admin_logger.log_playback_action(
                interaction.guild, "Pause", interaction.user
            )
        else:
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)
    
    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="music_skip", row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permissions(interaction):
            return
        
        state = self.cog.get_state(self.guild_id)
        
        # Log skip to admin channel before skipping
        if state.current:
            await self.cog.admin_logger.log_track_skip(
                interaction.guild, state.current, interaction.user, "Manual skip via button"
            )
        
        await state.skip()
        await interaction.response.send_message("⏭️ Skipped track.", ephemeral=True)
    
    @discord.ui.button(label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="music_loop", row=0)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permissions(interaction):
            return
        
        state = self.cog.get_state(self.guild_id)
        
        if state.loop_mode == LoopMode.OFF:
            state.loop_mode = LoopMode.TRACK
            msg = "🔂 Looping current track."
        elif state.loop_mode == LoopMode.TRACK:
            state.loop_mode = LoopMode.QUEUE
            msg = "🔁 Looping queue."
        else:
            state.loop_mode = LoopMode.OFF
            msg = "➡️ Loop disabled."
        
        await interaction.response.send_message(msg, ephemeral=True)
        # Update embed immediately to show new loop mode
        await state.update_embed_now()
        # Log to admin channel
        await self.cog.admin_logger.log_playback_action(
            interaction.guild, "Loop", interaction.user, 
            details=f"Mode: {state.loop_mode.name}"
        )
    
    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.secondary, custom_id="music_stop", row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permissions(interaction):
            return
        
        state = self.cog.get_state(self.guild_id)
        await state.clear_queue()
        
        if state.voice_client:
            state.voice_client.stop()
        
        state.current = None
        state.is_playing = False
        
        # Stop embed updates
        await state.stop_embed_updates()
        
        # Restore channel name when stopping
        await state.clear_channel_status()
        
        # Log to admin channel
        await self.cog.admin_logger.log_playback_action(
            interaction.guild, "Stop", interaction.user,
            details="Queue cleared"
        )
        
        # Send session report if there was activity
        await state.send_session_report(self.cog, "Music session ended - Playback stopped")
        
        await interaction.response.send_message("⏹️ Stopped playback and cleared queue.", ephemeral=True)
    
    @discord.ui.button(label="Add Song", emoji="➕", style=discord.ButtonStyle.secondary, custom_id="music_add", row=1)
    async def add_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You must be in a voice channel to add songs.", ephemeral=True)
            return
        
        state = self.cog.get_state(self.guild_id)
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        if interaction.user.voice.channel != state.voice_client.channel:
            await interaction.response.send_message("❌ You must be in the same voice channel as the bot.", ephemeral=True)
            return
        
        modal = AddSongModal(self.cog, self.guild_id, interaction.message)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Queue", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="music_queue", row=1)
    async def view_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.cog.get_state(self.guild_id)
        
        if not state.current and len(state.queue) == 0:
            await interaction.response.send_message("❌ Queue is empty.", ephemeral=True)
            return
        
        paginator = QueuePaginator(self.cog, self.guild_id, page=0)
        embed, total_pages = paginator.get_page_content(state)
        
        if total_pages <= 1:
            paginator.previous_page.disabled = True
            paginator.next_page.disabled = True
        else:
            paginator.previous_page.disabled = True
            paginator.next_page.disabled = False
        
        await interaction.response.send_message(embed=embed, view=paginator, ephemeral=True)
    
    @discord.ui.button(label="Leave", emoji="❌", style=discord.ButtonStyle.secondary, custom_id="music_leave", row=1)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_permissions(interaction):
            return
        
        state = self.cog.get_state(self.guild_id)
        
        if state.voice_client:
            channel = state.voice_client.channel
            
            # Log voice event to admin channel
            await self.cog.admin_logger.log_voice_event(
                interaction.guild, "Left", channel, interaction.user
            )
            
            # Restore channel name before leaving
            await state.clear_channel_status()
            
            # Send session report before leaving
            await state.send_session_report(self.cog, "Music session ended - Bot left voice channel")
            
            await state.voice_client.disconnect()
            state.voice_client = None
            await state.clear_queue()
            state.current = None
            state.is_playing = False
        
        await interaction.response.send_message("👋 Disconnected from voice channel.", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states: Dict[int, GuildMusicState] = {}
        self.state_lock = asyncio.Lock()
        self.ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
        
        # Download-first mode configuration
        self.download_first_enabled = os.getenv('DOWNLOAD_FIRST_MODE', 'true').lower() == 'true'
        print(f"Download-first mode: {'enabled' if self.download_first_enabled else 'disabled'}")
        
        # Control panel positioning
        self.keep_panel_at_bottom = os.getenv('KEEP_PANEL_AT_BOTTOM', 'true').lower() == 'true'
        print(f"Keep panel at bottom: {'enabled' if self.keep_panel_at_bottom else 'disabled'}")
        
        # Real-time embed updates
        self.realtime_embed_updates = os.getenv('REALTIME_EMBED_UPDATES', 'true').lower() == 'true'
        print(f"Real-time embed updates: {'enabled' if self.realtime_embed_updates else 'disabled'}")
        
        # Admin logging configuration
        self.admin_logger = AdminLogger(self.bot)
    
    async def cog_load(self):
        print("Music cog loaded successfully")
    
    async def cog_unload(self):
        print("Cleaning up music states...")
        async with self.state_lock:
            for guild_id, state in self.states.items():
                try:
                    # Stop embed updates
                    await state.stop_embed_updates()
                    
                    # Restore channel names before cleanup
                    await state.restore_channel_name()
                    
                    if state.voice_client:
                        await state.voice_client.disconnect()
                    if state.idle_task:
                        state.idle_task.cancel()
                    
                    # Clean up any downloaded files in queue
                    for track in state.queue:
                        if track.is_downloaded:
                            try:
                                track.cleanup()
                            except Exception as cleanup_error:
                                print(f"Error cleaning up track {track.title}: {cleanup_error}")
                    
                    # Clean up current track if downloaded
                    if state.current and state.current.is_downloaded:
                        try:
                            state.current.cleanup()
                        except Exception as cleanup_error:
                            print(f"Error cleaning up current track: {cleanup_error}")
                    
                    # Clean up channel manager
                    await state.cleanup_channel_manager()
                            
                except Exception as e:
                    print(f"Error cleaning up guild {guild_id}: {e}")
            self.states.clear()
        
        # Clean up all temporary audio files
        try:
            ytdl_source.cleanup_all_temp_files()
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
    
    def get_state(self, guild_id: int) -> GuildMusicState:
        if guild_id in self.states:
            return self.states[guild_id]
        
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState(self.bot)
        return self.states[guild_id]
    
    async def cleanup_state(self, guild_id: int):
        async with self.state_lock:
            if guild_id in self.states:
                state = self.states[guild_id]
                try:
                    # Stop embed updates
                    await state.stop_embed_updates()
                    
                    # Send session report
                    await state.send_session_report(self, "Music session ended - Bot cleanup")
                    
                    # Restore channel name before cleanup
                    await state.restore_channel_name()
                    
                    if state.voice_client:
                        await state.voice_client.disconnect()
                    if state.idle_task:
                        state.idle_task.cancel()
                    
                    # Clean up downloaded files before clearing queue
                    for track in state.queue:
                        if track.is_downloaded:
                            try:
                                track.cleanup()
                            except Exception as cleanup_error:
                                print(f"Error cleaning up track {track.title}: {cleanup_error}")
                    
                    if state.current and state.current.is_downloaded:
                        try:
                            state.current.cleanup()
                        except Exception as cleanup_error:
                            print(f"Error cleaning up current track: {cleanup_error}")
                    
                    # Clean up channel manager
                    await state.cleanup_channel_manager()
                    
                    await state.clear_queue()
                except Exception as e:
                    print(f"Error cleaning up state for guild {guild_id}: {e}")
                finally:
                    del self.states[guild_id]
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor messages to keep control panel at bottom of channel."""
        # Skip if feature is disabled
        if not hasattr(self, 'keep_panel_at_bottom') or not self.keep_panel_at_bottom:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Ignore bot's own messages
        if message.author.bot:
            return
        
        # Ignore commands (messages starting with /)
        if message.content.startswith('/'):
            return
        
        # Get state for this guild
        guild_id = message.guild.id
        if guild_id not in self.states:
            return
        
        state = self.states[guild_id]
        
        # Only proceed if music is playing and we have a control panel
        if not state.is_playing or not state.now_playing_message:
            return
        
        # Check if message is in the same channel as the control panel
        if message.channel.id != state.now_playing_message.channel.id:
            return
        
        # Move the control panel to the bottom (pass self as music_cog)
        await state.move_panel_to_bottom(self)
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        print(f"Bot removed from guild: {guild.name} (ID: {guild.id})")
        await self.cleanup_state(guild.id)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild_id = member.guild.id
        
        if member.id == self.bot.user.id:
            state = self.get_state(guild_id)
            
            if before.channel and not after.channel:
                # Bot was disconnected from voice channel
                # Log voice event to admin channel
                await self.admin_logger.log_voice_event(
                    member.guild, "Disconnected", before.channel
                )
                
                # Restore channel name if we were in a voice channel
                if before.channel and isinstance(before.channel, discord.VoiceChannel):
                    try:
                        await state.channel_manager.restore_original_name(before.channel)
                    except Exception as e:
                        print(f"Error restoring channel name on disconnect: {e}")
                
                state.voice_client = None
                
                # Send session report
                await state.send_session_report(self, "Music session ended - Bot disconnected from voice")
                
                await state.clear_queue()
                state.current = None
                state.is_playing = False
                return
            
            if not before.mute and after.mute:
                # Bot was server muted
                await self.admin_logger.log_playback_action(
                    member.guild, "Server Mute", member,
                    details="Bot was server muted, playback paused"
                )
                if state.voice_client and state.voice_client.is_playing():
                    state.voice_client.pause()
                    # Update embed to show paused state
                    await state.update_embed_now()
                return
            
            if before.mute and not after.mute:
                # Bot was server unmuted
                await self.admin_logger.log_playback_action(
                    member.guild, "Server Unmute", member,
                    details="Bot was server unmuted, playback resumed"
                )
                if state.voice_client and state.voice_client.is_paused():
                    state.voice_client.resume()
                    # Update embed to show playing state
                    await state.update_embed_now()
                return
            
            if not before.deaf and after.deaf:
                # Bot was server deafened
                await self.admin_logger.log_playback_action(
                    member.guild, "Server Deafen", member,
                    details="Bot was server deafened"
                )
                return
            
            if before.deaf and not after.deaf:
                # Bot was server undeafened
                await self.admin_logger.log_playback_action(
                    member.guild, "Server Undeafen", member,
                    details="Bot was server undeafened"
                )
                return
        
        if guild_id in self.states:
            state = self.states[guild_id]
            if state.voice_client and state.voice_client.channel:
                members = [m for m in state.voice_client.channel.members if not m.bot]
                
                if len(members) == 0:
                    print(f"[Guild {guild_id}] Bot alone in voice, will disconnect in 60s")
                    # Log to admin channel
                    await self.admin_logger.log_voice_event(
                        state.voice_client.guild, "Alone in Channel",
                        state.voice_client.channel,
                        None
                    )
                    await asyncio.sleep(60)
                    
                    if state.voice_client and state.voice_client.channel:
                        members = [m for m in state.voice_client.channel.members if not m.bot]
                        if len(members) == 0:
                            print(f"[Guild {guild_id}] Auto-leaving voice channel (alone)")
                            # Log auto-disconnect to admin channel
                            await self.admin_logger.log_voice_event(
                                state.voice_client.guild, "Auto-Disconnect (Alone)",
                                state.voice_client.channel,
                                None
                            )
                            
                            # Send session report
                            await state.send_session_report(self, "Music session ended - Bot alone in voice channel")
                            
                            await state.voice_client.disconnect()
                            await self.cleanup_state(guild_id)
    
    async def _ensure_voice(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You must be in a voice channel to use this command.", ephemeral=True)
            return False
        return True
    
    async def _play_next(self, guild_id: int):
        try:
            state = self.get_state(guild_id)
        except Exception as e:
            print(f"Error getting state for guild {guild_id}: {e}")
            return
        
        track = await state.next_track()
        
        if not track:
            state.is_playing = False
            state.reset_idle_timer()
            
            # Check if playlist just finished
            if state.playlist_finished and state.voice_client:
                # Log playlist completion - we don't have the old playlist info anymore
                # So just log that a playlist completed
                print(f"[Guild {guild_id}] Playlist completed")
                state.playlist_finished = False
            
            # Log queue finish to admin channel
            if state.voice_client:
                await self.admin_logger.log_playback_action(
                    state.voice_client.guild, "Queue Finished", state.voice_client.guild.me,
                    details="All tracks completed, playback stopped"
                )
            
            # Stop embed updates
            await state.stop_embed_updates()
            
            # Restore original channel name when playback ends
            await state.clear_channel_status()
            
            # Delete the now playing message to keep chat clean
            if state.now_playing_message:
                try:
                    await state.now_playing_message.delete()
                    state.now_playing_message = None
                except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                    print(f"Could not delete now playing message on queue finish: {e}")
            
            return
        
        # Create audio source
        try:
            # Check if voice client is still valid
            if not state.voice_client or not state.voice_client.is_connected():
                print(f"Voice client disconnected for guild {guild_id}")
                state.is_playing = False
                return
            
            # Use local file if downloaded, otherwise stream
            audio_source_path = track.get_audio_source()
            playback_mode = "local file" if track.is_downloaded else "stream"
            print(f"[Guild {guild_id}] Playing {track.title} from {playback_mode}: {audio_source_path}")
            
            # Use FFmpegPCMAudio with proper options for stable playback
            if track.is_downloaded:
                # For local files, use optimized options without reconnection
                audio_source = discord.FFmpegPCMAudio(
                    audio_source_path,
                    executable=self.ffmpeg_path,
                    **FFMPEG_LOCAL_OPTIONS
                )
            else:
                # For streams, use reconnection and async resampling options
                audio_source = discord.FFmpegPCMAudio(
                    audio_source_path,
                    executable=self.ffmpeg_path,
                    **FFMPEG_PCM_OPTIONS
                )
            
            # Wrap with volume transformer
            # Note: Volume transformer should NOT cause speed issues if FFmpeg settings are correct
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=state.volume)
            
            # Play the track
            def after_playing(error):
                if error:
                    print(f"[Guild {guild_id}] Playback error: {error}")
                
                # Clean up downloaded file after playback
                if track.is_downloaded:
                    try:
                        track.cleanup()
                    except Exception as cleanup_error:
                        print(f"[Guild {guild_id}] Cleanup error: {cleanup_error}")
                
                # Schedule next track (isolated per guild)
                future = asyncio.run_coroutine_threadsafe(
                    self._play_next(guild_id),
                    self.bot.loop
                )
                # Add error handler for the future
                try:
                    future.result(timeout=0.1)
                except:
                    pass
            
            state.voice_client.play(audio_source, after=after_playing)
            state.is_playing = True
            
            # Record track play for session tracking
            state.record_track_play(track)
            
            # Log track play to admin channel
            # If playlist, show position in playlist
            if state.current_playlist:
                position_str = f"Track {state.playlist_track_index} of {state.current_playlist['total']} (Playlist: {state.current_playlist['title'][:50]})"
            else:
                position_str = f"Session #{state.current_position}"
            
            await self.admin_logger.log_track_play(
                state.voice_client.guild,
                track,
                track.requester,
                state.current_position
            )
            
            # Cancel idle timer
            if state.idle_task:
                state.idle_task.cancel()
            
            # Update voice channel name to show current track
            await state.update_channel_name_for_track(track)
            
            # Send now playing embed with buttons
            await self._send_now_playing(state, track)
            
        except Exception as e:
            print(f"[Guild {guild_id}] Error playing track {track.title}: {e}")
            # Log error to admin channel
            if state.voice_client:
                await self.admin_logger.log_error(
                    state.voice_client.guild, "Playback Error", str(e),
                    context=f"Error playing track: {track.title}"
                )
            # Auto-skip to next track on error
            asyncio.create_task(self._play_next(guild_id))
            if state.now_playing_message:
                try:
                    # Update existing embed to show error state
                    embed = discord.Embed(
                        title="❌ Playback Error",
                        description=f"🚫 *Failed to play* **{track.title[:100]}**\n\n⏭️ Automatically skipping to next track...",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="🔧 Troubleshooting", value="This usually happens with unavailable videos", inline=False)
                    embed.set_footer(text="Skipping to next track automatically")
                    await state.now_playing_message.edit(embed=embed, view=None)
                except Exception as send_error:
                    print(f"[Guild {guild_id}] Error updating error message: {send_error}")
            
            # Try next track (with error handling)
            try:
                await self._play_next(guild_id)
            except Exception as next_error:
                print(f"[Guild {guild_id}] Error playing next track: {next_error}")
                state.is_playing = False
    
    async def _update_now_playing_embed(self, state: GuildMusicState):
        """Update the now playing embed with current queue info."""
        if not state.now_playing_message or not state.current:
            return
        
        try:
            # Get the current embed
            current_embed = state.now_playing_message.embeds[0] if state.now_playing_message.embeds else None
            if not current_embed:
                return
            
            # Update queue preview
            if len(current_embed.fields) >= 7:  # Make sure we have the "Up Next" field
                # Find and update the "Up Next" field (usually the last field before footer)
                for i, field in enumerate(current_embed.fields):
                    if field.name == "⏭️ Up Next":
                        if len(state.queue) > 0:
                            next_track = state.queue[0]
                            next_title = next_track.title[:35] + "..." if len(next_track.title) > 35 else next_track.title
                            next_info = f"**{next_title}**\n⏱️ `{next_track.duration_str}` • 👤 {next_track.requester.display_name}"
                            current_embed.set_field_at(i, name="⏭️ Up Next", value=next_info, inline=False)
                        else:
                            current_embed.set_field_at(i, name="⏭️ Up Next", value="*Queue is empty - add more songs!*", inline=False)
                        break
            
            # Update footer with new queue count and duration
            queue_duration = sum(t.duration for t in state.queue if t.duration)
            queue_time_str = YTDLSource.format_duration(queue_duration) if queue_duration > 0 else "0:00"
            playback_mode = "📁 Downloaded" if state.current.is_downloaded else "🌐 Streaming"
            footer_text = f"{playback_mode} • {len(state.queue)} in queue • {queue_time_str} remaining"
            current_embed.set_footer(text=footer_text, icon_url=state.current.requester.display_avatar.url)
            
            # Edit the message with updated embed
            await state.now_playing_message.edit(embed=current_embed)
            
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            print(f"Could not update now playing embed: {e}")
        except Exception as e:
            print(f"Unexpected error updating now playing embed: {e}")
    
    async def _send_now_playing(self, state: GuildMusicState, track: Track):
        """Send or update now playing embed with control buttons."""
        import time
        
        # Set track start time for progress calculation
        state.track_start_time = time.time()
        
        # Delete previous now playing message to keep chat clean
        if state.now_playing_message:
            try:
                await state.now_playing_message.delete()
                state.now_playing_message = None
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                print(f"Could not delete previous now playing message: {e}")
        
        # Create embed using the state's method
        embed = await state._create_now_playing_embed()
        if not embed:
            print("Failed to create now playing embed")
            return
        
        # Create buttons view
        view = ControlButtons(self, state.voice_client.guild.id)
        
        # Send message with better error handling
        try:
            # Use the stored text channel, or fall back to the previous message's channel
            if state.text_channel:
                channel = state.text_channel
            elif state.now_playing_message:
                channel = state.now_playing_message.channel
            else:
                # Last resort fallback
                channel = state.voice_client.guild.text_channels[0]
            
            message = await channel.send(embed=embed, view=view)
            state.now_playing_message = message
            
            # Start periodic embed updates (pass self as music_cog)
            await state.start_embed_updates(self)
            
        except discord.Forbidden:
            print(f"No permission to send messages in channel")
        except discord.HTTPException as e:
            print(f"HTTP error sending now playing message: {e}")
        except Exception as e:
            print(f"Unexpected error sending now playing message: {e}")
    
    @app_commands.command(name="play", description="Play a song or playlist from YouTube")
    @app_commands.describe(query="YouTube URL (video/playlist) or search term")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play a song or playlist from URL or search."""
        await interaction.response.defer()
        
        if not await self._ensure_voice(interaction):
            return
        
        state = self.get_state(interaction.guild.id)
        
        # Store the text channel where the command was used
        state.text_channel = interaction.channel
        
        # Connect to voice if not already
        if not state.voice_client:
            try:
                state.voice_client = await interaction.user.voice.channel.connect()
                # Log voice join to admin channel
                await self.admin_logger.log_voice_event(
                    interaction.guild, "Joined", interaction.user.voice.channel, interaction.user
                )
            except Exception as e:
                # Log error to admin channel
                await self.admin_logger.log_error(
                    interaction.guild, "Voice Connection Error", str(e),
                    context="Failed to connect to voice channel"
                )
                await interaction.followup.send(f"❌ Failed to connect to voice channel: {e}")
                return
        
        # Check if it's a playlist URL
        is_playlist = 'list=' in query or 'playlist' in query.lower()
        
        try:
            if is_playlist:
                # Fast playlist handling
                await self._handle_playlist(interaction, query, state)
            else:
                # Single track handling
                await self._handle_single_track(interaction, query, state)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    async def _handle_single_track(self, interaction: discord.Interaction, query: str, state: GuildMusicState, update_embed: Optional[discord.Message] = None):
        """Handle adding a single track with download-first approach."""
        track_info = None
        
        # Try download-first approach if enabled
        if self.download_first_enabled:
            track_info = await ytdl_source.download_track(query)
            
            # Fallback to streaming if download fails
            if not track_info:
                print(f"Download failed for {query}, falling back to streaming")
                track_info = await ytdl_source.get_track_info(query)
        else:
            # Use streaming mode
            track_info = await ytdl_source.get_track_info(query)
        
        if not track_info:
            embed = discord.Embed(
                title="❌ No Results Found",
                description="🔍 *Could not find any results for your query*",
                color=discord.Color.red()
            )
            embed.add_field(name="💡 Try:", value="• Different search terms\n• Direct YouTube URL\n• Check spelling", inline=False)
            embed.set_footer(text="Make sure the video is available and not private")
            await interaction.followup.send(embed=embed)
            return
        
        track = Track(track_info, interaction.user)
        # Store reference to ytdl_source for cleanup
        track._ytdl_source = ytdl_source
        await state.add_track(track)
        
        # Log queue update to admin channel
        await self.admin_logger.log_queue_update(
            interaction.guild, "Added", track, interaction.user
        )
        
        # Send enhanced confirmation with download status
        embed = discord.Embed(
            title="✅ Added to Queue",
            description=f"**[{track.title}]({track.webpage_url})**\n\n🎶 *Ready to play!*",
            color=discord.Color.green()
        )
        
        # Enhanced field layout
        embed.add_field(name="📺 Channel", value=f"`{track.uploader}`", inline=True)
        embed.add_field(name="⏱️ Duration", value=f"`{track.duration_str}`", inline=True)
        embed.add_field(name="📊 Queue Position", value=f"`#{len(state.queue)}`", inline=True)
        
        # Show download status with better formatting
        playback_mode = "📁 **Downloaded**" if track.is_downloaded else "🌐 **Streaming**"
        embed.add_field(name="🎵 Playback Mode", value=playback_mode, inline=True)
        
        # Show estimated wait time (fix: account for current track if playing)
        if len(state.queue) > 1:
            queue_before = state.queue[:-1]  # All tracks except the one just added
            wait_time = sum(t.duration for t in queue_before if t.duration)
            # Add current track remaining time if something is playing
            if state.current and state.current.duration:
                wait_time += state.current.duration
            wait_str = YTDLSource.format_duration(wait_time) if wait_time > 0 else "Soon"
            embed.add_field(name="⏰ Estimated Wait", value=f"`{wait_str}`", inline=True)
        elif state.current:
            embed.add_field(name="⏰ Status", value="`Playing Next!`", inline=True)
        else:
            embed.add_field(name="⏰ Status", value="`Playing Now!`", inline=True)
        
        embed.add_field(name="👤 Requested by", value=track.requester.mention, inline=True)
        
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        
        # Enhanced footer
        total_queue_time = sum(t.duration for t in state.queue if t.duration)
        queue_time_str = YTDLSource.format_duration(total_queue_time) if total_queue_time > 0 else "0:00"
        embed.set_footer(
            text=f"Queue: {len(state.queue)} tracks • Total time: {queue_time_str}",
            icon_url=track.requester.display_avatar.url
        )
        
        # If update_embed is provided, update the current now playing embed
        if update_embed:
            try:
                # Update the now playing embed with fresh queue info
                await self._update_now_playing_embed(state)
                # Send brief ephemeral confirmation
                await interaction.followup.send(
                    f"✅ **Added to queue:** {track.title[:50]}{'...' if len(track.title) > 50 else ''}",
                    ephemeral=True
                )
            except Exception as e:
                print(f"Error updating now playing embed: {e}")
        else:
            # Otherwise send confirmation as normal
            await interaction.followup.send(embed=embed)
        
        # Start playing if not already playing
        if not state.is_playing:
            await self._play_next(interaction.guild.id)
    
    async def _handle_playlist(self, interaction: discord.Interaction, url: str, state: GuildMusicState):
        """Handle adding a playlist with premium experience - no progressive loading messages."""
        # First, get playlist info quickly (just IDs and titles)
        playlist_info = await ytdl_source.get_playlist_info(url)
        
        if not playlist_info:
            # Not a playlist, try as single track
            await self._handle_single_track(interaction, url, state)
            return
        
        total_tracks = playlist_info['count']
        
        if total_tracks == 0:
            await interaction.followup.send("❌ Playlist is empty or unavailable.", ephemeral=True)
            return
        
        # Calculate total duration
        total_duration = 0
        for entry in playlist_info['entries']:
            if 'duration' in entry and entry['duration']:
                total_duration += entry['duration']
        
        # Set total tracks to playlist size FIRST (before adding any tracks)
        async with state.lock:
            state.total_tracks += total_tracks
        
        # Set current playlist metadata
        state.current_playlist = {
            'title': playlist_info['title'],
            'total': total_tracks,
            'added_by': interaction.user,
            'added_at': time.time(),
            'duration': total_duration
        }
        state.playlist_track_index = 0
        
        # Send clean, immediate feedback - NO progressive loading messages
        embed = discord.Embed(
            title="🎶 Playlist Added",
            description=f"**{playlist_info['title']}** — **{total_tracks} tracks** queued.",
            color=discord.Color.blue()
        )
        embed.add_field(name="📊 Total Tracks", value=f"`{total_tracks}`", inline=True)
        
        if total_duration > 0:
            duration_str = YTDLSource.format_duration(total_duration)
            embed.add_field(name="⏱️ Total Duration", value=f"`{duration_str}`", inline=True)
        
        embed.add_field(name="👤 Added by", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Tracks will load in background while playing")
        await interaction.followup.send(embed=embed)
        
        # Log playlist addition to admin channel
        await self.admin_logger.log_playlist_added(
            interaction.guild,
            playlist_info['title'],
            total_tracks,
            total_duration,
            interaction.user
        )
        
        # Fetch and add first track immediately for instant playback
        first_entry = playlist_info['entries'][0]
        # For playlists, use streaming for first track to start quickly
        first_track_info = await ytdl_source.get_track_info(first_entry['url'])
        
        if first_track_info:
            first_track = Track(first_track_info, interaction.user)
            first_track._ytdl_source = ytdl_source
            # Add track without incrementing total_tracks (already counted)
            async with state.lock:
                state.queue.append(first_track)
            
            # Start playing immediately
            if not state.is_playing:
                await self._play_next(interaction.guild.id)
        
        # Fetch remaining tracks in background (no progress messages)
        asyncio.create_task(self._fetch_playlist_tracks(
            playlist_info['entries'][1:],  # Skip first track
            interaction.user,
            state,
            interaction.channel,
            playlist_info['title'],
            total_tracks
        ))
    
    async def _fetch_playlist_tracks(
        self, 
        entries: list, 
        requester: discord.Member, 
        state: GuildMusicState,
        channel: discord.TextChannel,
        playlist_title: str,
        total_count: int
    ):
        """Fetch remaining playlist tracks in the background - NO progressive loading messages."""
        added_count = 1  # First track already added
        failed_count = 0
        guild_id = requester.guild.id
        
        print(f"[Guild {guild_id}] Fetching {len(entries)} remaining playlist tracks in background...")
        
        # Process in batches for efficiency - preload only a few at a time
        batch_size = 5  # Preload 5 tracks at a time for responsiveness
        
        for i, entry in enumerate(entries, start=2):
            try:
                # Check if state is still valid (bot might have left guild)
                if guild_id not in self.states:
                    print(f"[Guild {guild_id}] State removed, stopping playlist fetch")
                    break
                
                # If queue is getting large and we're far ahead, slow down
                while len(state.queue) > 20 and not state.is_playing:
                    await asyncio.sleep(1)  # Wait for playback to catch up
                
                track_info = await ytdl_source.get_track_info(entry['url'])
                
                if track_info:
                    track = Track(track_info, requester)
                    track._ytdl_source = ytdl_source
                    # Add track without incrementing total_tracks (already set for playlist)
                    async with state.lock:
                        state.queue.append(track)
                    added_count += 1
                    
                    # Log progress every 20 tracks (console only)
                    if i % 20 == 0:
                        print(f"[Guild {guild_id}] Loaded {i}/{total_count} tracks...")
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"[Guild {guild_id}] Failed to fetch track {entry.get('title', 'Unknown')}: {e}")
                failed_count += 1
                # Don't let one failure stop the whole playlist
                continue
        
        # NO completion message - keep channel clean
        # Just adjust total_tracks if some failed and log to console
        if failed_count > 0:
            async with state.lock:
                state.total_tracks -= failed_count
            print(f"[Guild {guild_id}] Playlist loaded: {added_count} added, {failed_count} failed")
        else:
            print(f"[Guild {guild_id}] Playlist loaded: {added_count} tracks, 100% success rate")
    
    @app_commands.command(name="pause", description="Pause the current track")
    async def pause(self, interaction: discord.Interaction):
        """Pause playback."""
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        if state.voice_client.is_playing():
            state.voice_client.pause()
            await interaction.response.send_message("⏸️ Paused playback.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)
    
    @app_commands.command(name="resume", description="Resume the paused track")
    async def resume(self, interaction: discord.Interaction):
        """Resume playback."""
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        if state.voice_client.is_paused():
            state.voice_client.resume()
            await interaction.response.send_message("▶️ Resumed playback.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Playback is not paused.", ephemeral=True)
    
    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction):
        """Skip current track."""
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client or not state.voice_client.is_playing():
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)
            return
        
        await state.skip()
        await interaction.response.send_message("⏭️ Skipped to next track.", ephemeral=True)
    
    @app_commands.command(name="stop", description="Stop playback and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        """Stop playback and clear queue."""
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        await state.clear_queue()
        state.voice_client.stop()
        state.current = None
        state.is_playing = False
        
        # Restore channel name when stopping
        await state.clear_channel_status()
        
        await interaction.response.send_message("⏹️ Stopped playback and cleared queue.", ephemeral=True)
    
    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: discord.Interaction):
        """Display the current queue with pagination."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current and len(state.queue) == 0:
            await interaction.response.send_message("❌ Queue is empty.", ephemeral=True)
            return
        
        # Create paginator
        paginator = QueuePaginator(self, interaction.guild.id, page=0)
        embed, total_pages = paginator.get_page_content(state)
        
        # Disable buttons if only one page
        if total_pages <= 1:
            paginator.previous_page.disabled = True
            paginator.next_page.disabled = True
        else:
            paginator.previous_page.disabled = True  # Start on first page
            paginator.next_page.disabled = False
        
        await interaction.response.send_message(embed=embed, view=paginator)
    
    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction):
        """Shuffle the queue."""
        state = self.get_state(interaction.guild.id)
        
        if len(state.queue) < 2:
            await interaction.response.send_message("❌ Not enough tracks in queue to shuffle.", ephemeral=True)
            return
        
        await state.shuffle_queue()
        await interaction.response.send_message(f"🔀 Shuffled {len(state.queue)} tracks.", ephemeral=True)
    
    @app_commands.command(name="loop", description="Toggle loop mode (off/track/queue)")
    @app_commands.describe(mode="Loop mode: off, track, or queue")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Track", value="track"),
        app_commands.Choice(name="Queue", value="queue"),
    ])
    async def loop(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        """Set loop mode."""
        state = self.get_state(interaction.guild.id)
        
        mode_map = {
            "off": (LoopMode.OFF, "➡️ Loop disabled."),
            "track": (LoopMode.TRACK, "🔂 Looping current track."),
            "queue": (LoopMode.QUEUE, "🔁 Looping queue."),
        }
        
        new_mode, message = mode_map[mode.value]
        state.loop_mode = new_mode
        
        await interaction.response.send_message(message, ephemeral=True)
    
    @app_commands.command(name="now", description="Show the currently playing track")
    async def now(self, interaction: discord.Interaction):
        """Show now playing track with enhanced info."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return
        
        track = state.current
        
        # Enhanced color scheme
        colors = [
            discord.Color.blue(), discord.Color.purple(), discord.Color.magenta(), 
            discord.Color.teal(), discord.Color.green(), discord.Color.orange(),
            discord.Color.red(), discord.Color.gold()
        ]
        color = colors[state.current_position % len(colors)]
        
        embed = discord.Embed(
            title="🎵 Currently Playing",
            description=f"**[{track.title}]({track.webpage_url})**\n\n🎶 *Now streaming for your enjoyment*",
            color=color
        )
        
        # First row
        embed.add_field(name="📺 Channel", value=f"`{track.uploader}`", inline=True)
        embed.add_field(name="⏱️ Duration", value=f"`{track.duration_str}`", inline=True)
        embed.add_field(name="👤 Requested by", value=track.requester.mention, inline=True)
        
        # Second row
        embed.add_field(name="📊 Track Position", value=f"`{state.current_position}` / `{state.total_tracks}`", inline=True)
        embed.add_field(name="🔊 Volume", value=f"`{int(state.volume * 100)}%`", inline=True)
        
        # Loop status with enhanced formatting
        loop_icons = {
            LoopMode.OFF: "➡️ **Off**",
            LoopMode.TRACK: "🔂 **Track**",
            LoopMode.QUEUE: "🔁 **Queue**"
        }
        embed.add_field(name="🔁 Loop Mode", value=loop_icons[state.loop_mode], inline=True)
        
        # Playback info
        playback_mode = "📁 **Downloaded**" if track.is_downloaded else "🌐 **Streaming**"
        embed.add_field(name="🎵 Playback Mode", value=playback_mode, inline=True)
        
        # Voice channel info
        if state.voice_client and state.voice_client.channel:
            channel_members = len([m for m in state.voice_client.channel.members if not m.bot])
            embed.add_field(name="🎧 Listeners", value=f"`{channel_members}` members", inline=True)
        
        # Queue preview
        if len(state.queue) > 0:
            next_track = state.queue[0]
            next_title = next_track.title[:30] + "..." if len(next_track.title) > 30 else next_track.title
            embed.add_field(name="⏭️ Up Next", value=f"**{next_title}**", inline=True)
        else:
            embed.add_field(name="⏭️ Up Next", value="*Queue empty*", inline=True)
        
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        
        # Enhanced footer with more details
        queue_duration = sum(t.duration for t in state.queue if t.duration)
        queue_time_str = YTDLSource.format_duration(queue_duration) if queue_duration > 0 else "0:00"
        
        footer_text = f"{len(state.queue)} tracks in queue • {queue_time_str} remaining"
        if state.voice_client and state.voice_client.channel:
            footer_text += f" • Connected to {state.voice_client.channel.name}"
        
        embed.set_footer(text=footer_text, icon_url=track.requester.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="volume", description="Set the playback volume (0-100)")
    @app_commands.describe(level="Volume level (0-100, default is 50)")
    async def volume(self, interaction: discord.Interaction, level: int):
        """Set playback volume."""
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        if level < 0 or level > 100:
            await interaction.response.send_message("❌ Volume must be between 0 and 100.", ephemeral=True)
            return
        
        # Update volume state
        state.volume = level / 100.0
        
        # If currently playing, update the volume in real-time
        if state.voice_client.source and isinstance(state.voice_client.source, discord.PCMVolumeTransformer):
            state.voice_client.source.volume = state.volume
        
        await interaction.response.send_message(f"🔊 Volume set to {level}%.", ephemeral=True)
    
    @app_commands.command(name="join", description="Join your current voice channel")
    async def join(self, interaction: discord.Interaction):
        """Join the user's voice channel."""
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You must be in a voice channel to use this command.", ephemeral=True)
            return
        
        state = self.get_state(interaction.guild.id)
        
        # If already connected to a voice channel
        if state.voice_client:
            if state.voice_client.channel == interaction.user.voice.channel:
                await interaction.response.send_message("✅ Already connected to your voice channel.", ephemeral=True)
                return
            else:
                # Move to the new channel
                await state.voice_client.move_to(interaction.user.voice.channel)
                await interaction.response.send_message(f"✅ Moved to {interaction.user.voice.channel.mention}.", ephemeral=True)
                return
        
        # Connect to voice channel
        try:
            state.voice_client = await interaction.user.voice.channel.connect()
            state.text_channel = interaction.channel
            # Log voice join to admin channel
            await self.admin_logger.log_voice_event(
                interaction.guild, "Joined", interaction.user.voice.channel, interaction.user
            )
            await interaction.response.send_message(f"✅ Joined {interaction.user.voice.channel.mention}.", ephemeral=True)
        except Exception as e:
            # Log error to admin channel
            await self.admin_logger.log_error(
                interaction.guild, "Voice Connection Error", str(e),
                context="Failed to join voice channel via /join command"
            )
            await interaction.response.send_message(f"❌ Failed to join voice channel: {e}", ephemeral=True)
    
    @app_commands.command(name="leave", description="Disconnect the bot from voice channel")
    async def leave(self, interaction: discord.Interaction):
        """Disconnect from voice."""
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        # Restore channel name before leaving
        await state.clear_channel_status()
        await state.voice_client.disconnect()
        state.voice_client = None
        await state.clear_queue()
        state.current = None
        state.is_playing = False
        
        await interaction.response.send_message("👋 Disconnected from voice channel.", ephemeral=True)
    
    @app_commands.command(name="remove", description="Remove a track from the queue by position")
    @app_commands.describe(position="Position of track to remove (1 for first in queue)")
    async def remove(self, interaction: discord.Interaction, position: int):
        """Remove a specific track from the queue."""
        state = self.get_state(interaction.guild.id)
        
        if len(state.queue) == 0:
            await interaction.response.send_message("❌ Queue is empty.", ephemeral=True)
            return
        
        if position < 1 or position > len(state.queue):
            await interaction.response.send_message(f"❌ Invalid position. Queue has {len(state.queue)} tracks.", ephemeral=True)
            return
        
        # Remove track (convert to 0-indexed)
        async with state.lock:
            removed_track = state.queue.pop(position - 1)
            state.total_tracks -= 1
        
        embed = discord.Embed(
            title="🗑️ Track Removed",
            description=f"🎵 *Successfully removed from queue*",
            color=discord.Color.orange()
        )
        
        title = removed_track.title[:50] + "..." if len(removed_track.title) > 50 else removed_track.title
        embed.add_field(name="🎶 Track", value=f"**{title}**", inline=False)
        embed.add_field(name="📊 Was at Position", value=f"`#{position}`", inline=True)
        embed.add_field(name="👤 Requested by", value=removed_track.requester.mention, inline=True)
        embed.set_footer(text=f"Queue now has {len(state.queue)} tracks")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="clear", description="Clear the entire queue")
    async def clear(self, interaction: discord.Interaction):
        """Clear the queue without stopping playback."""
        state = self.get_state(interaction.guild.id)
        
        if len(state.queue) == 0:
            await interaction.response.send_message("❌ Queue is already empty.", ephemeral=True)
            return
        
        cleared_count = len(state.queue)
        await state.clear_queue()
        
        embed = discord.Embed(
            title="🗑️ Queue Cleared",
            description=f"🧹 *Successfully cleared the queue*",
            color=discord.Color.orange()
        )
        embed.add_field(name="🗂️ Tracks Removed", value=f"`{cleared_count}` tracks", inline=True)
        embed.add_field(name="🎵 Current Track", value="*Still playing*" if state.current else "*None*", inline=True)
        embed.add_field(name="💡 Tip", value="Use `/stop` to stop current playback", inline=True)
        embed.set_footer(text="Queue is now empty - add songs with /play")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="voteskip", description="Vote to skip the current track")
    async def voteskip(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild.id)
        
        if not state.current:
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)
            return
        
        if not interaction.user.voice or not state.voice_client:
            await interaction.response.send_message("❌ You must be in the voice channel.", ephemeral=True)
            return
        
        if interaction.user.voice.channel != state.voice_client.channel:
            await interaction.response.send_message("❌ You must be in the same voice channel as the bot.", ephemeral=True)
            return
        
        members_count = len([m for m in state.voice_client.channel.members if not m.bot])
        needed = max(2, int(members_count * state.skip_threshold))
        
        state.skip_votes.add(interaction.user.id)
        votes = len(state.skip_votes)
        
        if votes >= needed:
            await state.skip()
            await interaction.response.send_message(f"⏭️ Skip vote passed! ({votes}/{needed})")
        else:
            await interaction.response.send_message(f"🗳️ Skip vote registered. ({votes}/{needed} needed)", ephemeral=True)
    
    @app_commands.command(name="previous", description="Play the previous track")
    async def previous(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        if not state.previous:
            await interaction.response.send_message("❌ No previous track available.", ephemeral=True)
            return
        
        async with state.lock:
            state.queue.insert(0, state.previous)
        
        await state.skip()
        await interaction.response.send_message(f"⏮️ Playing previous track: **{state.previous.title}**")
    
    @app_commands.command(name="pl-skip", description="Cancel and clear the entire playlist")
    async def pl_skip(self, interaction: discord.Interaction):
        """Cancel the entire playlist and clear all related tracks from queue."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current_playlist:
            await interaction.response.send_message("❌ No playlist is currently playing. Use `/skip` for single tracks.", ephemeral=True)
            return
        
        playlist_info = state.current_playlist
        tracks_remaining = len(state.queue)
        
        # Log playlist cancellation to admin channel
        await self.admin_logger.log_playlist_stopped(
            interaction.guild,
            playlist_info['title'],
            tracks_remaining,
            interaction.user,
            reason="Cancelled via /pl-skip"
        )
        
        # Stop current track
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.stop()
        
        # Clear the entire queue
        await state.clear_queue()
        
        # Reset playlist metadata
        state.current_playlist = None
        state.playlist_track_index = 0
        state.playlist_finished = False
        state.current = None
        state.is_playing = False
        
        # Stop embed updates
        await state.stop_embed_updates()
        
        # Delete the now playing message if it exists
        if state.now_playing_message:
            try:
                await state.now_playing_message.delete()
                state.now_playing_message = None
            except:
                pass
        
        # Send confirmation
        embed = discord.Embed(
            title="⏹️ Playlist Cancelled",
            description=f"🎶 *Entire playlist has been cleared*",
            color=discord.Color.orange()
        )
        embed.add_field(name="📜 Playlist", value=f"**{playlist_info['title']}**", inline=False)
        embed.add_field(name="🗑️ Tracks Removed", value=f"`{tracks_remaining}` tracks", inline=True)
        embed.add_field(name="👤 Cancelled by", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Use /play to start a new playlist or song")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pl-stop", description="Stop the playlist and clear its queue")
    async def pl_stop(self, interaction: discord.Interaction):
        """Stop playlist and clear queue."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current_playlist:
            await interaction.response.send_message("❌ No playlist is currently playing.", ephemeral=True)
            return
        
        playlist_info = state.current_playlist
        tracks_remaining = len(state.queue)
        
        # Log playlist stop to admin channel
        await self.admin_logger.log_playlist_stopped(
            interaction.guild,
            playlist_info['title'],
            tracks_remaining,
            interaction.user
        )
        
        # Clear playlist
        state.current_playlist = None
        state.playlist_track_index = 0
        
        # Clear queue and stop playback
        await state.clear_queue()
        
        if state.voice_client:
            state.voice_client.stop()
        
        state.current = None
        state.is_playing = False
        
        # Stop embed updates
        await state.stop_embed_updates()
        
        # Restore channel name
        await state.clear_channel_status()
        
        await interaction.response.send_message(
            f"⏹️ Stopped playlist: **{playlist_info['title']}**\n"
            f"📊 {tracks_remaining} tracks removed from queue",
            ephemeral=True
        )
    
    @app_commands.command(name="pl-now", description="Show currently playing track position in playlist")
    async def pl_now(self, interaction: discord.Interaction):
        """Show current track and position in playlist."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current_playlist:
            await interaction.response.send_message("❌ No playlist is currently playing.", ephemeral=True)
            return
        
        if not state.current:
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)
            return
        
        pl = state.current_playlist
        
        embed = discord.Embed(
            title="🎵 Current Playlist Track",
            description=f"**[{state.current.title}]({state.current.webpage_url})**",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📜 Playlist",
            value=f"`{pl['title'][:50]}`",
            inline=False
        )
        
        embed.add_field(
            name="📊 Position",
            value=f"**Track {state.playlist_track_index} of {pl['total']}**",
            inline=True
        )
        
        embed.add_field(
            name="⏭️ Remaining",
            value=f"`{len(state.queue)}` tracks",
            inline=True
        )
        
        embed.add_field(
            name="👤 Playlist Added By",
            value=pl['added_by'].mention,
            inline=True
        )
        
        if state.current.duration:
            elapsed = state.get_elapsed_time()
            remaining = state.get_remaining_time()
            progress_bar = state.create_progress_bar((elapsed / state.current.duration * 100))
            
            progress_text = f"{progress_bar}\n`{state.format_time(elapsed)}` / `{state.current.duration_str}`"
            embed.add_field(name="⏱️ Track Progress", value=progress_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="pl-info", description="Display playlist summary")
    async def pl_info(self, interaction: discord.Interaction):
        """Show playlist information."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current_playlist:
            await interaction.response.send_message("❌ No playlist is currently playing.", ephemeral=True)
            return
        
        pl = state.current_playlist
        
        def format_time(seconds: int) -> str:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {secs}s"
            return f"{minutes}m {secs}s"
        
        embed = discord.Embed(
            title="📜 Playlist Information",
            description=f"**{pl['title']}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Total Tracks",
            value=f"`{pl['total']}`",
            inline=True
        )
        
        if pl['duration'] > 0:
            embed.add_field(
                name="⏱️ Total Duration",
                value=f"`{format_time(pl['duration'])}`",
                inline=True
            )
        
        embed.add_field(
            name="👤 Added By",
            value=pl['added_by'].mention,
            inline=True
        )
        
        embed.add_field(
            name="🎵 Current Track",
            value=f"**{state.playlist_track_index}** of **{pl['total']}**",
            inline=True
        )
        
        embed.add_field(
            name="⏭️ Remaining",
            value=f"`{len(state.queue)}` tracks",
            inline=True
        )
        
        # Calculate elapsed playlist time
        import time
        elapsed_time = int(time.time() - pl['added_at'])
        embed.add_field(
            name="🕒 Playing For",
            value=f"`{format_time(elapsed_time)}`",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="pl-remove", description="Remove a specific track from the playlist queue")
    async def pl_remove(self, interaction: discord.Interaction, index: int):
        """Remove a track from playlist queue by index."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current_playlist:
            await interaction.response.send_message("❌ No playlist is currently playing.", ephemeral=True)
            return
        
        if index < 1 or index > len(state.queue):
            await interaction.response.send_message(
                f"❌ Invalid index. Queue has {len(state.queue)} tracks (1-{len(state.queue)})",
                ephemeral=True
            )
            return
        
        async with state.lock:
            removed_track = state.queue.pop(index - 1)
            state.total_tracks -= 1
        
        await interaction.response.send_message(
            f"🗑️ Removed track #{index}: **{removed_track.title}**",
            ephemeral=True
        )
        
        # Update embed to reflect queue change
        await state.update_embed_now()
    
    @app_commands.command(name="pl-jump", description="Jump directly to a specific track in the playlist")
    async def pl_jump(self, interaction: discord.Interaction, index: int):
        """Jump to a specific track in the playlist."""
        state = self.get_state(interaction.guild.id)
        
        if not state.current_playlist:
            await interaction.response.send_message("❌ No playlist is currently playing.", ephemeral=True)
            return
        
        if index < 1 or index > len(state.queue):
            await interaction.response.send_message(
                f"❌ Invalid index. Queue has {len(state.queue)} tracks (1-{len(state.queue)})",
                ephemeral=True
            )
            return
        
        # Remove all tracks before the target index
        async with state.lock:
            tracks_to_remove = index - 1
            for _ in range(tracks_to_remove):
                if state.queue:
                    state.queue.pop(0)
            
            # Adjust playlist index
            state.playlist_track_index = state.playlist_track_index + tracks_to_remove
        
        # Skip current track to start the target track
        await state.skip()
        
        target_track = state.queue[0] if state.queue else None
        if target_track:
            await interaction.response.send_message(
                f"⏩ Jumped to track #{index}: **{target_track.title}**",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Failed to jump to track.", ephemeral=True)
    
    @app_commands.command(name="history", description="Show recently played tracks")
    async def history(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild.id)
        
        if not state.history:
            await interaction.response.send_message("❌ No play history yet.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📜 Play History",
            description="🎵 *Recently played tracks*",
            color=discord.Color.blue()
        )
        
        history_text = ""
        recent_history = list(reversed(state.history[-10:]))
        for i, track in enumerate(recent_history, 1):
            title = track.title[:40] + "..." if len(track.title) > 40 else track.title
            history_text += f"`{i:2d}.` **{title}**\n"
            history_text += f"     📺 `{track.uploader}` • 👤 {track.requester.display_name}\n\n"
        
        embed.add_field(name="🎶 Recent Tracks", value=history_text.strip(), inline=False)
        
        if len(state.history) > 10:
            embed.add_field(
                name="📊 Total History", 
                value=f"*{len(state.history)} tracks played this session*", 
                inline=False
            )
        
        embed.set_footer(text=f"Showing last {len(recent_history)} of {len(state.history)} tracks played")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="move", description="Move a track to a new position in the queue")
    @app_commands.describe(from_pos="Current position of the track", to_pos="New position for the track")
    async def move(self, interaction: discord.Interaction, from_pos: int, to_pos: int):
        state = self.get_state(interaction.guild.id)
        
        if len(state.queue) == 0:
            await interaction.response.send_message("❌ Queue is empty.", ephemeral=True)
            return
        
        if from_pos < 1 or from_pos > len(state.queue) or to_pos < 1 or to_pos > len(state.queue):
            await interaction.response.send_message(f"❌ Invalid position. Queue has {len(state.queue)} tracks.", ephemeral=True)
            return
        
        async with state.lock:
            track = state.queue.pop(from_pos - 1)
            state.queue.insert(to_pos - 1, track)
        
        embed = discord.Embed(
            title="🔄 Track Moved",
            description=f"🎵 *Successfully repositioned in queue*",
            color=discord.Color.blue()
        )
        
        title = track.title[:45] + "..." if len(track.title) > 45 else track.title
        embed.add_field(name="🎶 Track", value=f"**{title}**", inline=False)
        embed.add_field(name="📊 From Position", value=f"`#{from_pos}`", inline=True)
        embed.add_field(name="📊 To Position", value=f"`#{to_pos}`", inline=True)
        embed.add_field(name="👤 Requested by", value=track.requester.mention, inline=True)
        embed.set_footer(text=f"Queue has {len(state.queue)} tracks")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="jump", description="Jump to a specific track in the queue")
    @app_commands.describe(position="Track position to jump to (1 for next track)")
    async def jump(self, interaction: discord.Interaction, position: int):
        state = self.get_state(interaction.guild.id)
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        if len(state.queue) == 0:
            await interaction.response.send_message("❌ Queue is empty.", ephemeral=True)
            return
        
        if position < 1 or position > len(state.queue):
            await interaction.response.send_message(f"❌ Invalid position. Queue has {len(state.queue)} tracks.", ephemeral=True)
            return
        
        async with state.lock:
            for _ in range(position - 1):
                state.queue.pop(0)
        
        await state.skip()
        await interaction.response.send_message(f"⏩ Jumping to position {position}")
    
    @app_commands.command(name="replay", description="Replay the current track from the beginning")
    async def replay(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild.id)
        
        if not state.current:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return
        
        if not state.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)
            return
        
        async with state.lock:
            state.queue.insert(0, state.current)
        
        await state.skip()
        await interaction.response.send_message(f"🔁 Replaying: **{state.current.title}**")


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    await bot.add_cog(Music(bot))
