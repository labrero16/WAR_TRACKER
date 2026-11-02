import discord
import requests
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CLASH_API = os.getenv("CLASH_API_KEY")

CHANNEL_ID = 1566014768404496384
CLAN_TAG = "PQ229"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

HEADERS = {
    "Authorization": f"Bearer {CLASH_API}"
}

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    while True:
        try:
            url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG}"

            response = requests.get(url, headers=HEADERS)

            if response.status_code == 200:
                clan = response.json()

                message = (
                    f"🏆 {clan['name']}\n"
                    f"👥 Members: {clan['members']}/50\n"
                    f"🏅 Clan Score: {clan['clanScore']}\n"
                    f"⭐ War Trophies: {clan['clanWarTrophies']}"
                )

                await channel.send(message)
            else:
                print(
                    f"API Error: {response.status_code} - "
                    f"{response.text}"
                )

        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(3600)

client.run(TOKEN)