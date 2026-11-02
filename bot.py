import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot online als {client.user}")

client.run(TOKEN)
