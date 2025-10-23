"""
Discord Music Bot - Main Entry Point
Loads cogs, syncs slash commands, and handles bot lifecycle.
"""

import asyncio
import os
import sys
import signal
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')  # Optional: for faster dev command syncing
OWNER_ID = os.getenv('OWNER_ID')  # Optional: bot owner ID

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not found in environment variables!")
    print("Please create a .env file with your bot token.")
    sys.exit(1)


class MusicBot(commands.Bot):
    """Custom bot class with startup and shutdown handlers."""
    
    def __init__(self):
        # Bot intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for some functionality
        intents.voice_states = True  # Required for voice
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",  # Prefix is not used since we only use slash commands
            intents=intents,
            help_command=None,  # Disable default help command
        )
        
        self.initial_extensions = [
            'cogs.music',
        ]
    
    async def setup_hook(self):
        """
        Called when the bot is starting up.
        Load cogs and sync slash commands.
        """
        print("Loading cogs...")
        
        # Load all cogs
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"✓ Loaded {extension}")
            except Exception as e:
                print(f"✗ Failed to load {extension}: {e}")
        
        # Sync slash commands
        print("\nSyncing slash commands...")
        try:
            if GUILD_ID:
                # Sync to specific guild for faster testing (dev mode)
                guild = discord.Object(id=int(GUILD_ID))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"✓ Synced commands to guild {GUILD_ID}")
            else:
                # Sync globally (takes up to 1 hour to propagate)
                await self.tree.sync()
                print("✓ Synced commands globally (may take up to 1 hour)")
        except Exception as e:
            print(f"✗ Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready and connected."""
        print(f"\n{'='*50}")
        print(f"Bot is ready!")
        print(f"Logged in as: {self.user.name} (ID: {self.user.id})")
        print(f"Connected to {len(self.guilds)} guild(s)")
        print(f"{'='*50}\n")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/play to add music"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Global error handler for commands."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        print(f"Command error: {error}")
    
    async def close(self):
        """Graceful shutdown handler."""
        print("\nShutting down bot...")
        
        # Disconnect all voice clients
        for voice_client in self.voice_clients:
            try:
                await voice_client.disconnect()
            except:
                pass
        
        # Clean up music cog and temp files
        music_cog = self.get_cog('Music')
        if music_cog:
            try:
                await music_cog.cog_unload()
            except Exception as e:
                print(f"Error during music cog cleanup: {e}")
        
        await super().close()
        print("Bot shutdown complete.")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)


async def main():
    """Main function to run the bot."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start bot
    bot = MusicBot()
    
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received.")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
