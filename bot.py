import asyncio
from datetime import datetime
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


@tree.command(
    name="warpunten",
    description="Toon de punten van de laatste war"
)
async def warpunten(interaction: discord.Interaction):

    headers = {
        "Authorization": f"Bearer {CLASH_API_KEY}"
    }

    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG}/riverracelog"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        await interaction.response.send_message(
            f"❌ API-fout ({response.status_code})"
        )
        return

    data = response.json()

    if not data.get("items"):
        await interaction.response.send_message(
            "❌ Geen war-geschiedenis gevonden."
        )
        return

    laatste_war = data["items"][0]

    standings = laatste_war.get("standings", [])

    eigen_clan = None

    for standing in standings:
        clan = standing.get("clan", {})

        if clan.get("tag", "").replace("#", "") == CLAN_TAG:
            eigen_clan = clan
            break

    if not eigen_clan:
        await interaction.response.send_message(
            "❌ Jouw clan werd niet gevonden in de laatste war."
        )
        return

    deelnemers = eigen_clan.get("participants", [])

    if not deelnemers:
        await interaction.response.send_message(
            "⚠️ De Clash Royale API geeft geen deelnemers terug voor deze war."
        )
        return

    deelnemers = sorted(
        deelnemers,
        key=lambda x: x.get("fame", 0),
        reverse=True
    )

    bericht = "🏆 **Laatste War - Punten per speler**\n\n"

    for speler in deelnemers:
        naam = speler.get("name", "Onbekend")
        fame = speler.get("fame", 0)

        bericht += f"**{naam}** - {fame} punten\n"

    if len(bericht) > 1900:
        bericht = bericht[:1900]

    await interaction.response.send_message(bericht)


client.run(TOKEN)
