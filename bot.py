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

    try:
        response = requests.get(url, headers=headers, timeout=15)

        channel = discord.utils.get(
            client.get_all_channels(),
            name="lab-war-stats"
        )

        if channel:
            await channel.send(
                f"🔍 Clash Royale API test\nStatuscode: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()

                await channel.send(
                    f"✅ API werkt!\n"
                    f"Clan: {data['name']}\n"
                    f"Leden: {data['members']}\n"
                    f"Trophies: {data['clanScore']}"
                )
            else:
                await channel.send(
                    f"❌ API fout\n"
                    f"Statuscode: {response.status_code}\n"
                    f"Antwoord: {response.text}"
                )

    except Exception as e:
        print(e)

        channel = discord.utils.get(
            client.get_all_channels(),
            name="lab-war-stats"
        )

        if channel:
            await channel.send(f"❌ Fout: {e}")


client.run(TOKEN)
