import discord
import requests
import asyncio

DISCORD_TOKEN = "DISCORD_TOKEN"
CR_API_TOKEN = "CLASH_API_TOKEN"
CHANNEL_ID = CHANNEL_ID

CLAN_TAG = "PQ229"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def get_river_race():
    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG}/currentriverrace"

    headers = {
        "Authorization": f"Bearer {CR_API_TOKEN}"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return "Kan River Race data niet ophalen."

    data = r.json()

    clans = data.get("clans", [])

    msg = "🏆 River Race Stand\n\n"

    for i, clan in enumerate(clans, start=1):
        name = clan["name"]
        fame = clan.get("fame", 0)

        msg += f"{i}. {name} - {fame} fame\n"

    return msg


@client.event
async def on_ready():
    print(f"Bot online als {client.user}")

    while True:
        channel = client.get_channel(CHANNEL_ID)

        if channel:
            await channel.send(get_river_race())

        await asyncio.sleep(86400)


client.run(DISCORD_TOKEN)
