"""
YouTube and audio stream utilities using yt-dlp.
Handles URL extraction, metadata fetching, and search functionality.
"""

import asyncio
import functools
import os
import tempfile
import shutil
from typing import Optional, Dict, Any
import yt_dlp


# yt-dlp options for extracting audio stream info (streaming mode)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,  # For single tracks only
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extract_flat': False,  # We need full info, not just IDs
    'skip_download': True,  # We only need the URL, not the file
    'cookiefile': os.getenv('YT_COOKIES_PATH', './cookies.txt') if os.path.exists(os.getenv('YT_COOKIES_PATH', './cookies.txt')) else None,  # Cookie file for YouTube auth
}

# yt-dlp options for downloading audio files (download-first mode)
YTDL_DOWNLOAD_OPTIONS = {
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'skip_download': False,  # We want to download the file
    'outtmpl': '%(title)s.%(ext)s',  # Will be overridden with temp path
    'cookiefile': os.getenv('YT_COOKIES_PATH', './cookies.txt') if os.path.exists(os.getenv('YT_COOKIES_PATH', './cookies.txt')) else None,  # Cookie file for YouTube auth
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

# Fast playlist options - extract only basic info first
YTDL_PLAYLIST_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,  # Fast extraction - gets all entries with basic info
    'skip_download': True,
    'playlistend': None,  # No limit on playlist entries
    'cookiefile': os.getenv('YT_COOKIES_PATH', './cookies.txt') if os.path.exists(os.getenv('YT_COOKIES_PATH', './cookies.txt')) else None,  # Cookie file for YouTube auth
}

# FFmpeg options for stable Discord voice streaming
# Simple, proven configuration that prevents speed and cut issues
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 128k'
}

# PCM-specific options for FFmpegPCMAudio
# Discord requires: 48kHz, stereo, 16-bit PCM
# Enhanced options to prevent speed bumps and audio cuts
FFMPEG_PCM_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 48000 -ac 2 -af "aresample=async=1:min_hard_comp=0.100000:first_pts=0"'
}

# Local file playback options - optimized for stability
FFMPEG_LOCAL_OPTIONS = {
    'before_options': '',
    'options': '-vn -ar 48000 -ac 2 -bufsize 512k'
}


class YTDLSource:
    """Wrapper for yt-dlp to extract audio stream information and download files.
    
    Thread Safety: This class uses run_in_executor to run blocking yt-dlp
    operations in a thread pool, making it safe for concurrent use across
    multiple guilds. Each extract_info call runs in isolation.
    
    Download-First Mode: Supports downloading audio files to temporary storage
    for stable playback without streaming issues.
    """
    
    def __init__(self):
        self.ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
        self.ytdl_playlist = yt_dlp.YoutubeDL(YTDL_PLAYLIST_OPTIONS)
        self.ytdl_download = None  # Will be created per download with temp path
        
        # Create temp directory for audio files
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'discord_bot_audio')
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"Audio temp directory: {self.temp_dir}")
    
    async def extract_info(self, url: str, download: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract video/audio information from a URL or search query.
        
        Args:
            url: YouTube URL or search query
            download: Whether to download (we never do for streaming)
            
        Returns:
            Dictionary containing video metadata and stream URL
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Run yt-dlp extraction in thread pool to avoid blocking
            data = await loop.run_in_executor(
                None,
                functools.partial(self.ytdl.extract_info, url, download=download)
            )
            
            if data is None:
                return None
            
            # If it's a search result, get the first entry
            if 'entries' in data:
                if len(data['entries']) == 0:
                    return None
                data = data['entries'][0]
            
            return data
            
        except Exception as e:
            print(f"Error extracting info from {url}: {e}")
            return None
    
    async def get_track_info(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get track information suitable for playback.
        
        Args:
            query: URL or search term
            
        Returns:
            Dictionary with keys: title, url, duration, thumbnail, webpage_url
        """
        data = await self.extract_info(query, download=False)
        
        if not data:
            return None
        
        # Extract relevant fields
        track_info = {
            'title': data.get('title', 'Unknown'),
            'url': data.get('url'),  # Direct audio stream URL
            'duration': data.get('duration', 0),
            'thumbnail': data.get('thumbnail'),
            'webpage_url': data.get('webpage_url', query),
            'uploader': data.get('uploader', 'Unknown'),
        }
        
        return track_info
    
    async def get_playlist_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get playlist information quickly using flat extraction.
        
        Args:
            url: Playlist URL
            
        Returns:
            Dictionary with playlist title and list of video URLs
        """
        loop = asyncio.get_event_loop()
        
        try:
            # First, do fast flat extraction to get video IDs
            data = await loop.run_in_executor(
                None,
                functools.partial(self.ytdl_playlist.extract_info, url, download=False)
            )
            
            if not data:
                return None
            
            # Check if it's a playlist
            if 'entries' not in data:
                # Single video, not a playlist
                return None
            
            playlist_info = {
                'title': data.get('title', 'Unknown Playlist'),
                'entries': [],
                'count': 0
            }
            
            # Extract video URLs from flat data
            for entry in data['entries']:
                if entry:  # Skip None entries (deleted/private videos)
                    video_id = entry.get('id')
                    video_url = entry.get('url')
                    
                    # Construct proper URL
                    if not video_url and video_id:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                    elif not video_url:
                        continue  # Skip if no URL or ID
                    
                    # Store minimal info - we'll fetch full details later
                    playlist_info['entries'].append({
                        'url': video_url,
                        'title': entry.get('title', 'Unknown'),
                        'id': video_id
                    })
            
            playlist_info['count'] = len(playlist_info['entries'])
            print(f"Extracted {playlist_info['count']} tracks from playlist: {playlist_info['title']}")
            return playlist_info
            
        except Exception as e:
            print(f"Error extracting playlist info: {e}")
            return None
    
    async def download_track(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Download audio track to temporary file for stable playback.
        
        Args:
            query: URL or search term
            
        Returns:
            Dictionary with track info including local file path
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Create a unique temp directory for this download
            download_dir = tempfile.mkdtemp(dir=self.temp_dir)
            
            # Configure download options with temp path
            download_options = YTDL_DOWNLOAD_OPTIONS.copy()
            download_options['outtmpl'] = os.path.join(download_dir, '%(title)s.%(ext)s')
            
            # Create downloader instance
            ytdl_downloader = yt_dlp.YoutubeDL(download_options)
            
            # Download the track
            data = await loop.run_in_executor(
                None,
                functools.partial(ytdl_downloader.extract_info, query, download=True)
            )
            
            if data is None:
                shutil.rmtree(download_dir, ignore_errors=True)
                return None
            
            # If it's a search result, get the first entry
            if 'entries' in data:
                if len(data['entries']) == 0:
                    shutil.rmtree(download_dir, ignore_errors=True)
                    return None
                data = data['entries'][0]
            
            # Find the downloaded file
            downloaded_file = None
            for file in os.listdir(download_dir):
                if file.endswith(('.mp3', '.m4a', '.webm', '.opus')):
                    downloaded_file = os.path.join(download_dir, file)
                    break
            
            if not downloaded_file or not os.path.exists(downloaded_file):
                print(f"Downloaded file not found in {download_dir}")
                shutil.rmtree(download_dir, ignore_errors=True)
                return None
            
            # Extract relevant fields
            track_info = {
                'title': data.get('title', 'Unknown'),
                'url': data.get('url'),  # Original stream URL (backup)
                'local_file': downloaded_file,  # Path to downloaded file
                'temp_dir': download_dir,  # Directory to cleanup later
                'duration': data.get('duration', 0),
                'thumbnail': data.get('thumbnail'),
                'webpage_url': data.get('webpage_url', query),
                'uploader': data.get('uploader', 'Unknown'),
                'is_downloaded': True,
            }
            
            print(f"Downloaded: {track_info['title']} -> {downloaded_file}")
            return track_info
            
        except Exception as e:
            print(f"Error downloading track from {query}: {e}")
            # Cleanup on error
            if 'download_dir' in locals():
                shutil.rmtree(download_dir, ignore_errors=True)
            return None
    
    def cleanup_track_file(self, track_info: Dict[str, Any]):
        """
        Clean up downloaded track file and temp directory.
        
        Args:
            track_info: Track info dictionary with temp_dir
        """
        if track_info.get('is_downloaded') and track_info.get('temp_dir'):
            try:
                temp_dir = track_info['temp_dir']
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    print(f"Cleaned up temp files: {temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temp files: {e}")
    
    def cleanup_all_temp_files(self):
        """
        Clean up all temporary audio files (called on bot shutdown).
        """
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                print(f"Cleaned up all temp audio files: {self.temp_dir}")
        except Exception as e:
            print(f"Error cleaning up all temp files: {e}")
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS or MM:SS."""
        if seconds is None or seconds == 0:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


# Global instance
ytdl_source = YTDLSource()
