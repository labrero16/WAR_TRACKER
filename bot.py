import asyncio
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
import requests
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
CLASH_API_KEY = os.getenv("CLASH_API_KEY")

if not os.getenv("CHANNEL_ID"):
    raise Exception("CHANNEL_ID secret ontbreekt")

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

CLAN_TAG = "PQ229"
TIMEZONE = ZoneInfo("Europe/Brussels")

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def api_get(endpoint):

    headers = {
        "Authorization": f"Bearer {CLASH_API_KEY}"
    }

    url = f"https://api.clashroyale.com/v1/{endpoint}"

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        return response

    except Exception as e:
        print(f"API verbinding mislukt: {e}")
        return None


@client.event
async def on_ready():

    await tree.sync()

    print(f"Bot online als {client.user}")

    if not hasattr(client, "daily_task_started"):
        client.daily_task_started = True
        asyncio.create_task(dagelijkse_melding())


async def stuur_deck_melding():

    response = api_get(
        f"clans/%23{CLAN_TAG}/currentriverrace"
    )

    if response is None:
        return

    if response.status_code != 200:
        print(
            f"API fout: {response.status_code} - {response.text}"
        )
        return

    data = response.json()

    eigen_clan = None

    for clan in data.get("clans", []):

        if clan.get("tag", "").replace("#", "") == CLAN_TAG:
            eigen_clan = clan
            break

    if not eigen_clan:
        return

    deelnemers = eigen_clan.get("participants", [])

    spelers_met_decks = []

    for speler in deelnemers:

        naam = speler.get("name", "Onbekend")

        resterend = speler.get("decksRemainingToday")

        if resterend is None:
            gebruikt = speler.get("decksUsedToday", 0)
            resterend = max(0, 4 - gebruikt)

        if resterend > 0:

            spelers_met_decks.append(
                f"• **{naam}** ({resterend} decks over)"
            )

    if spelers_met_decks:

        bericht = (
            "⚠️ **Spelers met resterende war decks**\n\n"
            + "\n".join(spelers_met_decks)
        )

    else:

        bericht = (
            "✅ Iedereen heeft alle war decks gespeeld."
        )

    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send(bericht)


async def dagelijkse_melding():

    await client.wait_until_ready()

    while not client.is_closed():

        nu = datetime.now(TIMEZONE)

        if nu.hour == 12 and nu.minute == 30:

            await stuur_deck_melding()

            # voorkomt dubbele melding
            await asyncio.sleep(60)

        await asyncio.sleep(20)


@tree.command(
    name="war",
    description="Toon de huidige River Race stand"
)
async def war(interaction: discord.Interaction):

    await interaction.response.defer()

    response = api_get(
        f"clans/%23{CLAN_TAG}/currentriverrace"
    )

    if response is None:

        await interaction.followup.send(
            "❌ Verbindingsfout met Clash Royale API."
        )
        return

    if response.status_code != 200:

        await interaction.followup.send(
            f"❌ API-fout ({response.status_code})\n{response.text}"
        )
        return

    data = response.json()

    clans = sorted(
        data.get("clans", []),
        key=lambda x: x.get("fame", 0),
        reverse=True
    )

    embed = discord.Embed(
        title="🏆 River Race Stand",
        color=0xffd700
    )

    for positie, clan in enumerate(clans, start=1):

        naam = clan.get("name", "Onbekend")
        fame = clan.get("fame", 0)

        embed.add_field(
            name=f"{positie}. {naam}",
            value=f"Fame: {fame}",
            inline=False
        )

    await interaction.followup.send(
        embed=embed
    )


@tree.command(
    name="warpunten",
    description="Toon de punten van de laatste war"
)
async def warpunten(interaction: discord.Interaction):

    await interaction.response.defer()

    response = api_get(
        f"clans/%23{CLAN_TAG}/riverracelog"
    )

    if response is None:

        await interaction.followup.send(
            "❌ Verbindingsfout met Clash Royale API."
        )
        return

    if response.status_code != 200:

        await interaction.followup.send(
            f"❌ API-fout ({response.status_code})\n{response.text}"
        )
        return

    data = response.json()

    if not data.get("items"):

        await interaction.followup.send(
            "❌ Geen war-geschiedenis gevonden."
        )
        return

    laatste_war = data["items"][0]

    standings = laatste_war.get(
        "standings",
        []
    )

    eigen_clan = None

    for standing in standings:

        clan = standing.get("clan", {})

        if clan.get(
            "tag",
            ""
        ).replace("#", "") == CLAN_TAG:

            eigen_clan = clan
            break

    if not eigen_clan:

        await interaction.followup.send(
            "❌ Jouw clan werd niet gevonden."
        )
        return

    deelnemers = eigen_clan.get(
        "participants",
        []
    )

    if not deelnemers:

        await interaction.followup.send(
            "⚠️ Geen deelnemers gevonden."
        )
        return

    deelnemers = sorted(
        deelnemers,
        key=lambda x: x.get("fame", 0),
        reverse=True
    )

    bericht = (
        "🏆 **Laatste War - Punten per speler**\n\n"
    )

    for speler in deelnemers:

        naam = speler.get(
            "name",
            "Onbekend"
        )

        fame = speler.get(
            "fame",
            0
        )

        bericht += (
            f"**{naam}** - {fame} punten\n"
        )

    if len(bericht) > 1900:
        bericht = bericht[:1900]

    await interaction.followup.send(
        bericht
    )


client.run(TOKEN)
