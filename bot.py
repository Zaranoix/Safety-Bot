import os
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo      # make sure you’ve installed tzdata if needed
import traceback
import time as _time   # for sleeping on crash

# ─── Configuration ─────────────────────────────────────────────────────────────

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1260994184920170507
CHANNEL_NAME = "sussy-city"

# ZoneInfo for America/Chicago (handles CST/CDT)
CST = ZoneInfo("America/Chicago")

# ─── State for skipping first run ───────────────────────────────────────────────

last_scheduled_refresh_date = None

# ─── Bot & Intents ─────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Channel Refresh Helper ────────────────────────────────────────────────────

async def refresh_all_text_channels(guild: discord.Guild):
    now_iso = datetime.now(tz=CST).isoformat()
    for ch in list(guild.text_channels):
        await ch.delete()
        print(f"{now_iso} 🗑️ Deleted channel {ch.name} (ID: {ch.id})")
    await guild.create_text_channel(CHANNEL_NAME)
    print(f"{now_iso} ✅ Created channel {CHANNEL_NAME}")

# ─── Midnight Scheduler ────────────────────────────────────────────────────────

@tasks.loop(time=dt_time(hour=0, minute=0, tzinfo=CST))
async def midnight_refresh():
    global last_scheduled_refresh_date
    now = datetime.now(tz=CST)

    # skip the initial invocation on startup
    if now.date() == last_scheduled_refresh_date:
        print(f"{now.isoformat()} ⏰ Skipping initial scheduled run (already ran today)")
        return

    guild = bot.get_guild(GUILD_ID)
    if guild:
        await refresh_all_text_channels(guild)
        last_scheduled_refresh_date = now.date()
        print(f"{now.isoformat()} 🎉 Midnight refresh complete")

        # ─── Shutdown PC ───────────────────────────────────────────────────────
        # Immediately shut down the Windows machine
        os.system("shutdown /s /t 0")
    else:
        print(f"{now.isoformat()} ⚠️ Guild {GUILD_ID} not found—cannot refresh")

# ─── Events ───────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    global last_scheduled_refresh_date
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if not getattr(bot, "midnight_started", False):
        # mark today so the very first scheduled call is skipped
        last_scheduled_refresh_date = datetime.now(tz=CST).date()
        midnight_refresh.start()
        bot.midnight_started = True
        print(f"{datetime.now(tz=CST).isoformat()} 🏁 Midnight scheduler started")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip().lower() == "!re":
        guild = bot.get_guild(GUILD_ID)
        if guild:
            await refresh_all_text_channels(guild)
            now = datetime.now(tz=CST).isoformat()
            print(f"{now} 🔄 Manual refresh triggered by {message.author}")

    await bot.process_commands(message)

# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    while True:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"⚠️ Bot crashed: {e}")
            traceback.print_exc()
            _time.sleep(5)
            print("🔄 Restarting bot...")
