import json
import os
import platform
import traceback
from dotenv import load_dotenv
from discord.ext import commands
import discord

import logger
from config import Configuration

intents = discord.Intents.default()
intents.message_content = True

config = {}
with open('config.json', 'r') as f:
    config = f.read()
with open('config.json.old', 'w') as f:
    f.write(config)
config = Configuration(config)


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.prefix),
            intents=intents,
            help_command=None,
        )
        self.logger = logger.logger
        self.config: Configuration = config
        self.logger.info("Prefix: " + self.config.prefix)

        with open('config.json', 'w') as f:
            f.write(json.dumps(self.config.to_dict(), indent=4))


    async def load_cogs(self) -> None:
        """
        The code in this function is executed whenever the bot will start.
        """
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    self.logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(
                        f"Failed to load extension {extension}\n{exception}"
                    )
                    traceback.print_exc()

    async def setup_hook(self) -> None:
        """
        This will just be executed when the bot starts the first time.
        """
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"discord.py API version: {discord.__version__}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(
            f"Running on: {platform.system()} {platform.release()} ({os.name})"
        )
        self.logger.info("-------------------")
        await self.load_cogs() 

    
    @commands.command(name="save")
    async def save(self, ctx: commands.Context):
        with open('config.json', 'w') as f:
            f.write(json.dumps(self.config.to_dict(), indent=4))


load_dotenv()

bot = DiscordBot()

@bot.command(name="sync")
async def tree_sync(ctx):
        try:
            #.tree.copy_global_to(guild=Snowflake(1259941990515216475))
            #synced = await bot.tree.sync(guild=1259941990515216475)
            #await ctx.send(f'Successfully synced to guild {len(synced)} commands.')

            synced = await bot.tree.sync()
            await ctx.send(f'Successfully synced {len(synced)} commands.')
        except Exception as e:
            pass
            await ctx.send(f'An error occurred: {str(e)}')


bot.run(os.getenv("TOKEN"))