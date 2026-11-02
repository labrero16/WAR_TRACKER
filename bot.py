import os
import discord
import requests
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
CLASH_API_KEY = os.getenv("CLASH_API_KEY")

CLAN_TAG = "PQ229"

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot online als {client.user}")


@tree.command(
    name="war",
    description="Toon de huidige River Race stand"
)
async def war(interaction: discord.Interaction):

    headers = {
        "Authorization": f"Bearer {CLASH_API_KEY}"
    }

    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG}/currentriverrace"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        await interaction.response.send_message(
            f"❌ API-fout ({response.status_code})"
        )
        return

    data = response.json()

    embed = discord.Embed(
        title="🏆 River Race Stand",
        color=0xffd700
    )

    clans = data.get("clans", [])

    for position, clan in enumerate(clans, start=1):
        name = clan.get("name", "Onbekend")
        fame = clan.get("fame", 0)

        embed.add_field(
            name=f"{position}. {name}",
            value=f"Fame: {fame}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


client.run(TOKEN)
