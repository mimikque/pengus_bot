from datetime import datetime
import random
import traceback
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from typing import Literal, Optional


# Here we name the cog and create a new class for the cog.
class Ticket(commands.Cog, name="buyer"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.bot.orders = {}
        self.message_orders = {}

    @commands.command(name="ticket_setup")
    async def ticket_setup(self, ctx: commands.Context) -> None:
        #TODO send ticket Embed/View
        pass


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Ticket(bot))