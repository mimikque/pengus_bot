import os
from dotenv import load_dotenv
from discord.ext import commands
import discord

import logger

intents = discord.Intents.default()
intents.message_content = True

config = {
    "prefix": "!",
}


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(config["prefix"]),
            intents=intents,
            help_command=None,
        )
        self.logger = logger.logger
        self.config = config
        self.logger.info("Prefix: " + config["prefix"])


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

    @status_task.before_loop
    async def before_status_task(self) -> None:
        """
        Before starting the status changing task, we make sure the bot is ready
        """
        await self.wait_until_ready()

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
        self.status_task.start()    
    
    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context[commands.Bot]) -> None:
        """Pong!"""
        await ctx.send("Pong!")


load_dotenv()

bot = DiscordBot()

@bot.command(name="sync")
async def tree_sync(ctx):
        bot.logger.info("COMMAND RUN!")
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