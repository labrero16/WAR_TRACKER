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

    import json

    data = response.json()

    print("\n========== START API DATA ==========")
    print(json.dumps(data, indent=2))
    print("========== EINDE API DATA ==========\n")

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

@tree.command(
    name="colosseum",
    description="Geavanceerde colosseum analyse"
)
async def colosseum(interaction: discord.Interaction):

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

    eigen_clan = None
    eigen_positie = None

    for i, clan in enumerate(clans):

        if clan.get("tag", "").replace("#", "") == CLAN_TAG:
            eigen_clan = clan
            eigen_positie = i + 1
            break

    if eigen_clan is None:

        await interaction.followup.send(
            "❌ Eigen clan niet gevonden."
        )
        return

    deelnemers = eigen_clan.get("participants", [])

    huidige_score = eigen_clan.get("fame", 0)

    totaal_resterende_decks = 0
    actieve_spelers = 0

    totale_fame = 0
    totale_gebruikte_decks = 0

    spelers_over = []

    for speler in deelnemers:

        naam = speler.get("name", "Onbekend")
        fame = speler.get("fame", 0)
        gebruikt = speler.get("decksUsedToday", 0)

        resterend = speler.get("decksRemainingToday")

        if resterend is None:
            resterend = max(0, 4 - gebruikt)

        totale_fame += fame
        totale_gebruikte_decks += gebruikt
        totaal_resterende_decks += resterend

        if resterend > 0:

            actieve_spelers += 1

            spelers_over.append(
                f"• {naam} ({resterend})"
            )

    if totale_gebruikte_decks > 0:

        fame_per_deck = (
            totale_fame / totale_gebruikte_decks
        )

    else:

        fame_per_deck = 200

    verwachte_extra_fame = int(
        totaal_resterende_decks * fame_per_deck
    )

    verwachte_eindscore = (
        huidige_score + verwachte_extra_fame
    )

    leider = clans[0]

    leider_naam = leider.get(
        "name",
        "Onbekend"
    )

    leider_fame = leider.get(
        "fame",
        0
    )

    if huidige_score == 0:

        achterstand = 0

        kans_tekst = (
            "ℹ️ Er zijn nog geen war battles gespeeld."
        )

    elif leider.get("tag", "").replace("#", "") == CLAN_TAG:

        achterstand = 0

        kans_tekst = (
            "🥇 Jullie staan momenteel op de eerste plaats."
        )

    else:

        achterstand = max(
            0,
            leider_fame - huidige_score
        )

        if verwachte_extra_fame >= achterstand * 2:

            kans_tekst = (
                "✅ Zeer grote kans om de leider te pakken."
            )

        elif verwachte_extra_fame >= achterstand:

            kans_tekst = (
                "⚠️ Kans aanwezig als spelers hun decks gebruiken."
            )

        else:

            kans_tekst = (
                "❌ Leider lijkt voorlopig buiten bereik."
            )

    embed = discord.Embed(
        title="🏟️ Colosseum Analyse",
        color=0x3498db
    )

    embed.add_field(
        name="📍 Huidige positie",
        value=str(eigen_positie),
        inline=True
    )

    embed.add_field(
        name="🏆 Huidige score",
        value=f"{huidige_score:,}".replace(",", "."),
        inline=True
    )

    embed.add_field(
        name="🎴 Resterende decks",
        value=str(totaal_resterende_decks),
        inline=True
    )

    embed.add_field(
        name="👥 Actieve spelers",
        value=str(actieve_spelers),
        inline=True
    )

    embed.add_field(
        name="⚔️ Gem. fame/deck",
        value=f"{fame_per_deck:.1f}",
        inline=True
    )

    embed.add_field(
        name="📈 Verwachte extra fame",
        value=f"{verwachte_extra_fame:,}".replace(",", "."),
        inline=True
    )

    embed.add_field(
        name="🎯 Verwachte eindscore",
        value=f"{verwachte_eindscore:,}".replace(",", "."),
        inline=False
    )

    if achterstand > 0:

        embed.add_field(
            name=f"🥇 Leider: {leider_naam}",
            value=(
                f"{leider_fame:,}".replace(",", ".")
                + f"\nAchterstand: {achterstand:,}".replace(",", ".")
            ),
            inline=False
        )

    embed.add_field(
        name="🔮 Prognose",
        value=kans_tekst,
        inline=False
    )

    if spelers_over:

        lijst = "\n".join(
            spelers_over[:15]
        )

        embed.add_field(
            name="⚠️ Spelers met decks over",
            value=lijst,
            inline=False
        )

    await interaction.followup.send(
        embed=embed
    )

@tree.command(
    name="boat",
    description="Analyse van boat attacks versus gewone battles"
)
async def boat(interaction: discord.Interaction):

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

    eigen_clan = None

    for clan in data.get("clans", []):

        if clan.get("tag", "").replace("#", "") == CLAN_TAG:
            eigen_clan = clan
            break

    if eigen_clan is None:

        await interaction.followup.send(
            "❌ Eigen clan niet gevonden."
        )
        return

    deelnemers = eigen_clan.get("participants", [])

    totaal_fame = 0
    totaal_gebruikte_decks = 0
    totaal_resterende_decks = 0
    totaal_boat_attacks = 0
    totaal_repair_points = 0

    spelers_met_decks = []

    for speler in deelnemers:

        naam = speler.get(
            "name",
            "Onbekend"
        )

        fame = speler.get(
            "fame",
            0
        )

        gebruikt = speler.get(
            "decksUsedToday",
            0
        )

        resterend = speler.get(
            "decksRemainingToday"
        )

        if resterend is None:
            resterend = max(
                0,
                4 - gebruikt
            )

        boat_attacks = speler.get(
            "boatAttacks",
            0
        )

        repair_points = speler.get(
            "repairPoints",
            0
        )

        totaal_fame += fame
        totaal_gebruikte_decks += gebruikt
        totaal_resterende_decks += resterend
        totaal_boat_attacks += boat_attacks
        totaal_repair_points += repair_points

        if resterend > 0:

            spelers_met_decks.append(
                (naam, resterend)
            )

    if totaal_gebruikte_decks > 0:

        fame_per_deck = (
            totaal_fame /
            totaal_gebruikte_decks
        )

    else:

        fame_per_deck = 200

    maximale_extra_fame = int(
        totaal_resterende_decks *
        fame_per_deck
    )

    kost_1_boat = int(
        fame_per_deck
    )

    kost_5_boat = int(
        fame_per_deck * 5
    )

    kost_10_boat = int(
        fame_per_deck * 10
    )

    kost_20_boat = int(
        fame_per_deck * 20
    )

    spelers_met_decks = sorted(
        spelers_met_decks,
        key=lambda x: x[1],
        reverse=True
    )

    embed = discord.Embed(
        title="🚢 Boat Analyse",
        color=0x0099ff
    )

    embed.add_field(
        name="⚔️ Gem. fame/deck",
        value=f"{fame_per_deck:.1f}",
        inline=True
    )

    embed.add_field(
        name="🎴 Resterende decks",
        value=str(
            totaal_resterende_decks
        ),
        inline=True
    )

    embed.add_field(
        name="📈 Maximale fame",
        value=f"{maximale_extra_fame:,}".replace(
            ",",
            "."
        ),
        inline=True
    )

    embed.add_field(
        name="🚢 Boat attacks",
        value=str(
            totaal_boat_attacks
        ),
        inline=True
    )

    embed.add_field(
        name="🔧 Repair points",
        value=str(
            totaal

client.run(TOKEN)
