import random
from typing import List
from discord.ext import commands
import discord
from discord import ui

from pengus_bot.src.config import TicketConfiguration
from pengus_bot.src.main import DiscordBot

# Here we name the cog and create a new class for the cog.
class Ticket(commands.Cog, name="ticket"):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot = bot
        self.ticket: TicketConfiguration = bot.config.ticket
    
    @commands.command(name="ticket_setup")
    async def ticket_setup(self, ctx: commands.Context, ticket_category: str):
        category = ""

        if ticket_category == self.bot.config["create_one_for_me"]:
            category = await ctx.guild.create_category(name="tickets")
        else:
            category = discord.utils.get(ctx.guild.categories, name=ticket_category)

        self.ticket.ticket_category_id = category.id
        await self.setup_ticket_channel(ctx.channel)
    
    async def setup_ticket_channel(self, channel: discord.TextChannel):
        await channel.send(
            embed = discord.Embed(
                title="Ticket",
                color=discord.Color.green(),
                description="beschreibung oder so... idk"
            ),
            view = TicketChannelView(
                    self.ticket.topics,
                    discord.utils.get(channel.guild, id = self.ticket.get_ticket_category(channel.guild))
                )
        )


class TicketChannelView(ui.View):
    def __init__(self, topics: List[discord.SelectOption], ticket_category: discord.CategoryChannel):
        super().__init__()
        self.ticket_category: discord.CategoryChannel = ticket_category

        self.add_item(
            ui.Select(
                placeholder ="Make a selection",
                options = topics,
                custom_id ="topic_select"
            )
        )
    
    @discord.ui.select(custom_id="topic_select")
    async def topic_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()

        topic = select.values[0]
        if (ch := self.already_has_ticket_for(topic, interaction.user.id)) != None:
            await interaction.followup.send(f'You already have a ticket in {ch.mention}', ephemeral=True)
            return
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
            interaction.user.id: discord.PermissionOverwrite(read_messages=True)
        }

        if self.config["moderator_role"] != None:
            overwrites[discord.utils.get(interaction.guild.roles, id = self.config.roles.moderator)] = discord.PermissionOverwrite(read_messages=True)
        
        channel = await self.ticket_category.create_text_channel(
            name  = f'#{''.join(random.choices('0123456789', k=5))}',
            topic = f'{interaction.user.id}:{topic}',
            overwrites = overwrites,
        )

    
    def already_has_ticket_for(self, topic, user_id):
        for ch in self.ticket_category.text_channels:
            if ch.topic == f'{user_id}:{topic}':
                return ch
        return False