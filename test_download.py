#!/usr/bin/env python3
"""
Test script for the download-first playback system.
This script tests the YTDLSource download functionality without requiring Discord.
"""

import asyncio
import os
import sys
from utils.yt import ytdl_source

async def test_download_functionality():
    """Test the download functionality with a sample video."""
    print("🧪 Testing Download-First Playback System")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Rick Astley Never Gonna Give You Up",  # Search query
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Direct URL
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 30)
        
        try:
            # Test download
            print("⬇️  Attempting download...")
            track_info = await ytdl_source.download_track(query)
            
            if track_info:
                print("✅ Download successful!")
                print(f"   Title: {track_info['title']}")
                print(f"   Duration: {track_info['duration']}s")
                print(f"   Local file: {track_info['local_file']}")
                print(f"   File exists: {os.path.exists(track_info['local_file'])}")
                
                # Test cleanup
                print("🧹 Testing cleanup...")
                ytdl_source.cleanup_track_file(track_info)
                print(f"   File exists after cleanup: {os.path.exists(track_info['local_file'])}")
                print("✅ Cleanup successful!")
                
            else:
                print("❌ Download failed!")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
    
    # Test streaming fallback
    print(f"\n📝 Test 3: Streaming fallback")
    print("-" * 30)
    
    try:
        print("🌐 Testing streaming mode...")
        track_info = await ytdl_source.get_track_info("Rick Astley Never Gonna Give You Up")
        
        if track_info:
            print("✅ Streaming mode successful!")
            print(f"   Title: {track_info['title']}")
            print(f"   Stream URL: {track_info['url'][:50]}...")
            print(f"   Is downloaded: {track_info.get('is_downloaded', False)}")
        else:
            print("❌ Streaming mode failed!")
            
    except Exception as e:
        print(f"❌ Error during streaming test: {e}")
    
    # Cleanup all temp files
    print(f"\n🧹 Final cleanup...")
    try:
        ytdl_source.cleanup_all_temp_files()
        print("✅ All temp files cleaned up!")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

async def test_temp_directory():
    """Test temporary directory creation and management."""
    print("\n🗂️  Testing temporary directory management...")
    
    temp_dir = ytdl_source.temp_dir
    print(f"   Temp directory: {temp_dir}")
    print(f"   Directory exists: {os.path.exists(temp_dir)}")
    
    if os.path.exists(temp_dir):
        files = os.listdir(temp_dir)
        print(f"   Files in temp dir: {len(files)}")
        if files:
            print(f"   Files: {files}")

def main():
    """Main test function."""
    print("🎵 Discord Music Bot - Download System Test")
    print("This script tests the download-first playback functionality.")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("utils/yt.py"):
        print("❌ Error: Please run this script from the bot's root directory")
        print("   Expected: python test_download.py")
        sys.exit(1)
    
    # Test temp directory
    asyncio.run(test_temp_directory())
    
    # Run download tests
    try:
        asyncio.run(test_download_functionality())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
