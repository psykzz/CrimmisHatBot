import os

import discord
from discord.ext import commands

users = {}

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = commands.when_mentioned_or("!"),
            intents = discord.Intents.all(),
            help_command = commands.DefaultHelpCommand(dm_help=True)
        )

    async def setup_hook(self) -> None:
        print(f"\033[31mLogged in as {client.user}\033[39m")
        await client.load_extension(f"cogs.hat")

    async def on_ready(self):
        print("Logged on as {}".format(self.user))
        game = discord.Game(name="'!hathelp' for info!")
        await self.change_presence(activity=game)



if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise Exception("Missing Discord token")
    client = Bot()
    client.run(token)

