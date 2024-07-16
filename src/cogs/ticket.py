from datetime import datetime
import random
import traceback
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from typing import Literal, Optional
import discord.ui as ui
from discord import app_commands


# Here we name the cog and create a new class for the cog.
class Ticket(commands.Cog, name="ticket"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.bot.orders = {}
        self.bot.message_orders = {}

    @commands.hybrid_command(name="ticket_setup")
    async def ticket_setup(self, ctx: commands.Context, ticket_category: str) -> None:
        category = ""
        if ticket_category == self.bot.config["create_one_for_me"]:
            category = await ctx.guild.create_category(
                name = "tickets"
            )
        else:
            category = discord.utils.get(ctx.guild.categories, name=ticket_category)

        
        self.bot.set_json("ticket_category", category.id)
        await ctx.send(
            embed = discord.Embed(
                title="Ticket",
                color=discord.Color.green(),
                description="beschreibung oder so... idk"
            ),
            view = CreateTicketView(self.bot.config)
        )
    
    @commands.hybrid_command(name="mod_role")
    async def mod_role(self, ctx: commands.Context, moderator_role: str) -> None:
        role = discord.utils.get(ctx.guild.roles, name=moderator_role)
        self.bot.config["moderator_role"] = role.id
    

    @ticket_setup.autocomplete(name='ticket_category')
    async def ticket_category_autocomplete(self, interaction: discord.Interaction, current: str):
        categories = [category.name for category in interaction.guild.categories]
        categories.append(self.bot.config["create_one_for_me"])
        return [
            app_commands.Choice(name=category, value=category)
            for category in categories if current.lower() in category.lower()
        ]
    
    @mod_role.autocomplete(name='moderator_role')
    async def moderator_role_autocomplete(self, interaction: discord.Interaction, current: str):
        categories = [category.name for category in interaction.guild.roles]
        return [
            app_commands.Choice(name=category, value=category)
            for category in categories if current.lower() in category.lower()
        ]


class CreateTicketView(ui.View):    
    def __init__(self, config):
        super().__init__()
        self.config = config


    @ui.select(
            options = [
                discord.SelectOption(label="Staff Application", value="staff_application", description="Apply to be part of the staff team"),
                discord.SelectOption(label="Tier Test", value="tier_test", description="Take a test to prove your skills"),
                discord.SelectOption(label="Other Questions", value="other_questions", description="Ask any other questions")
            ],
            placeholder="Make a selection"
    )
    async def topic_select(self, interaction: discord.Interaction, select: ui.Select):
        await interaction.response.defer()

        topic = select.values[0]
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id = self.config["ticket_category"])
        for ch in category.text_channels:
            if ch.topic == f'{interaction.user.id}:{topic}':
                await interaction.followup.send(f'You already have a ticket in {ch.mention}', ephemeral=True)
                return
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
        }
        if self.config["moderator_role"] != None:
            overwrites[discord.utils.get(interaction.guild.roles, id = self.config["moderator_config"])] = discord.PermissionOverwrite(read_messages=True),
        channel = await category.create_text_channel(
            name  = f'#0000',
            topic = f'{interaction.user.id}:{topic}',
            overwrites = overwrites,
        )

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Ticket(bot))