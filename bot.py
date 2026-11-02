import os
import discord
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CLASH_API_KEY = os.getenv("CLASH_API_KEY")

CLAN_TAG = "PQ229"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot online als {client.user}")

    headers = {
        "Authorization": f"Bearer {CLASH_API_KEY}"
    }

    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG}"

    response = requests.get(url, headers=headers)

    print("Status:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        print("Clan:", data["name"])
    else:
        print(response.text)

client.run(TOKEN)
