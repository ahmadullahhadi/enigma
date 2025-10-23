#!/usr/bin/env python3
"""
Test script for the voice channel name update feature.
This script tests the VoiceChannelManager functionality without requiring Discord.
"""

import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock
from cogs.music import VoiceChannelManager, Track

class MockVoiceChannel:
    """Mock Discord VoiceChannel for testing."""
    
    def __init__(self, channel_id: int, name: str):
        self.id = channel_id
        self.name = name
        self._original_name = name
    
    async def edit(self, *, name: str, reason: str = None):
        """Mock channel edit method."""
        print(f"[MockChannel] Renaming channel: {self.name} -> {name} (Reason: {reason})")
        self.name = name
    
    def __str__(self):
        return f"MockVoiceChannel(id={self.id}, name='{self.name}')"

class MockTrack:
    """Mock Track for testing."""
    
    def __init__(self, title: str):
        self.title = title
    
    def __str__(self):
        return f"MockTrack(title='{self.title}')"

async def test_channel_manager():
    """Test the VoiceChannelManager functionality."""
    print("🧪 Testing Voice Channel Name Updates")
    print("=" * 50)
    
    # Create test instances
    manager = VoiceChannelManager()
    channel = MockVoiceChannel(12345, "General Voice")
    
    # Test data
    test_tracks = [
        MockTrack("Never Gonna Give You Up"),
        MockTrack("Bohemian Rhapsody"),
        MockTrack("Song with Special Characters: <>/\\|?*"),
        MockTrack("Very Long Song Title That Exceeds The Normal Length Limit For Discord Channel Names And Should Be Truncated Properly"),
    ]
    
    print(f"\n📝 Initial Setup")
    print(f"   Channel: {channel}")
    print(f"   Manager enabled: {manager.enabled}")
    print(f"   Rename cooldown: {manager.rename_cooldown}s")
    
    # Test 1: Store original name
    print(f"\n📝 Test 1: Store Original Name")
    await manager.store_original_name(channel)
    print(f"   Stored names: {manager.original_names}")
    
    # Test 2: Update channel for each track
    for i, track in enumerate(test_tracks, 1):
        print(f"\n📝 Test {i + 1}: Update Channel for Track")
        print(f"   Track: {track}")
        
        # Test sanitization
        sanitized = manager.sanitize_track_name(track.title)
        print(f"   Sanitized title: '{sanitized}'")
        
        # Test channel update
        await manager.update_channel_for_track(channel, track)
        print(f"   Channel after update: {channel}")
        
        # Small delay to test cooldown (optional)
        if i < len(test_tracks) - 1:
            print("   Waiting 1 second...")
            await asyncio.sleep(1)
    
    # Test 3: Restore original name
    print(f"\n📝 Test {len(test_tracks) + 2}: Restore Original Name")
    await manager.restore_original_name(channel)
    print(f"   Channel after restore: {channel}")
    
    # Test 4: Cooldown functionality
    print(f"\n📝 Test {len(test_tracks) + 3}: Cooldown Functionality")
    print("   Testing rapid updates (should be blocked by cooldown)...")
    
    track = MockTrack("Test Cooldown Song")
    
    # First update should work
    await manager.update_channel_for_track(channel, track)
    print(f"   First update: {channel}")
    
    # Immediate second update should be blocked
    track2 = MockTrack("Another Song")
    await manager.update_channel_for_track(channel, track2)
    print(f"   Second update (should be blocked): {channel}")
    
    # Test 5: Cleanup
    print(f"\n📝 Test {len(test_tracks) + 4}: Cleanup")
    print(f"   Before cleanup - stored names: {len(manager.original_names)}")
    print(f"   Before cleanup - rename times: {len(manager.last_rename_time)}")
    
    manager.cleanup_channel(channel.id)
    print(f"   After cleanup - stored names: {len(manager.original_names)}")
    print(f"   After cleanup - rename times: {len(manager.last_rename_time)}")
    
    print("\n" + "=" * 50)
    print("🎉 Channel name tests completed!")

async def test_sanitization():
    """Test the track name sanitization."""
    print("\n🧹 Testing Track Name Sanitization")
    print("-" * 30)
    
    manager = VoiceChannelManager()
    
    test_cases = [
        ("Normal Song Title", "Normal Song Title"),
        ("Song with <special> characters", "Song with special characters"),
        ("Path/with\\slashes", "Pathwithslashes"),
        ("Song: with | pipes * and ? marks", "Song with  pipes  and  marks"),
        ("A" * 100, "A" * 47 + "..."),  # Test length limit
        ("", ""),  # Empty string
        ("🎵 Song with emoji 🎶", "🎵 Song with emoji 🎶"),  # Emojis should be preserved
    ]
    
    for original, expected in test_cases:
        result = manager.sanitize_track_name(original)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{original}' -> '{result}'")
        if result != expected:
            print(f"      Expected: '{expected}'")

def main():
    """Main test function."""
    print("🎵 Discord Music Bot - Channel Name Feature Test")
    print("This script tests the voice channel name update functionality.")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("cogs/music.py"):
        print("❌ Error: Please run this script from the bot's root directory")
        print("   Expected: python test_channel_names.py")
        sys.exit(1)
    
    # Run tests
    try:
        asyncio.run(test_sanitization())
        asyncio.run(test_channel_manager())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
