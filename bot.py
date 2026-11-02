import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

CHANNEL_ID = 1419362848173621248  # vervang door jouw kanaal-ID

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot online als {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send("@everybody ✅ Lab War Tracker is online!")

client.run(TOKEN)
