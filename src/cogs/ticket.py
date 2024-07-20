import random
from typing import List
from datetime import datetime
import random
import discord
from discord.ext import commands
import discord.ui as ui
from discord import app_commands

from config import Configuration, TicketConfiguration



# Here we name the cog and create a new class for the cog.
class Ticket(commands.Cog, name="ticket"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config: Configuration = bot.config
        self.ticket: TicketConfiguration = self.config.ticket
    
    @app_commands.command(name="ticket_setup")
    async def ticket_setup(self, interaction: discord.Interaction, ticket_category: str):
        await interaction.response.defer()
        category = ""

        if ticket_category == self.ticket.create_one_for_me:
            category = await interaction.guild.create_category(name="tickets")
        else:
            category = discord.utils.get(interaction.guild.categories, name=ticket_category)
        self.ticket.ticket_category_id = category.id

        message: discord.WebhookMessage = await interaction.followup.send("Creating view", ephemeral=True)
        await self.setup_ticket_channel(interaction.channel)
        await message.delete()
        await interaction.followup.send("Completed setup", ephemeral=True)
    
    @ticket_setup.autocomplete(name='ticket_category')
    async def ticket_category_autocomplete(self, interaction: discord.Interaction, current: str):
        categories = [category.name for category in interaction.guild.categories]
        categories.append(self.ticket.create_one_for_me)
        return [
            app_commands.Choice(name=category, value=category)
            for category in categories if current.lower() in category.lower()
        ]
    
    @app_commands.command(name="moderator_role")
    async def moderator_role(self, interaction: discord.Interaction, moderator_role: str):
        moderator = ""

        if moderator_role == self.ticket.create_one_for_me:
            moderator = await interaction.guild.create_role(name="ticket moderator")
            await interaction.response.send_message(f"Created role {moderator.mention}.", ephemeral=True)
        else:
            moderator = discord.utils.get(interaction.guild.roles, name=moderator_role)
            await interaction.response.send_message(f"Please use `!save` to store the configuration!", ephemeral=True)

        self.config.roles.moderator = moderator.id
        
    
    @moderator_role.autocomplete(name='moderator_role')
    async def moderator_role_autocomplete(self, interaction: discord.Interaction, current: str):
        categories = [category.name for category in interaction.guild.roles]
        categories.append(self.ticket.create_one_for_me)
        return [
            app_commands.Choice(name=category, value=category)
            for category in categories if current.lower() in category.lower()
        ]


    async def setup_ticket_channel(self, channel: discord.TextChannel):
        view = TicketChannelView(
                    self.ticket.topics,
                    self.ticket.get_ticket_category(channel.guild),
                    self.config.roles.get_moderator(channel.guild)
                )
        self.bot.add_view(view)
        await channel.send(
            embed = discord.Embed(
                title="Ticket",
                color=discord.Colour.green(),
                description="beschreibung oder so... idk"
            ),
            view = view
        )


class TicketChannelView(ui.View):
    def __init__(self, topics: List[discord.SelectOption], ticket_category: discord.CategoryChannel, moderator_role = None):
        super().__init__(timeout=None)
        self.ticket_category: discord.CategoryChannel = ticket_category
        self.moderator_role = moderator_role
        self.topics = topics


        self.select = ui.Select(
                placeholder ="Make a selection",
                options = topics,
                custom_id ="topic_select"
            )
        self.select.callback = self.topic_select_callback
        self.add_item(self.select)
        
    
    async def topic_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        topic = self.select.values[0]
        if (ch := self.already_has_ticket_for(topic, interaction.user.id)) != None:
            await interaction.followup.send(f'You already have a ticket in {ch.mention}', ephemeral=True)
            return
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True)
        }

        if self.moderator_role != None:
            overwrites[self.moderator_role] = discord.PermissionOverwrite(read_messages=True)
        
        channel = await self.ticket_category.create_text_channel(
            name  = f'#{''.join(random.choices('0123456789', k=5))}',
            topic = f'{interaction.user.id}:{topic}',
            overwrites = overwrites,
        )
        
        await self.reset_view(interaction.message)
    
    async def reset_view(self, message: discord.Message):
        self.select = ui.Select(
                placeholder ="Make a selection",
                options = self.topics,
                custom_id ="topic_select"
            )
        self.select.callback = self.topic_select_callback
        self.clear_items()
        self.add_item(self.select)

        await message.edit(view=self)

    
    def already_has_ticket_for(self, topic, user_id):
        for ch in self.ticket_category.text_channels:
            if ch.topic == f'{user_id}:{topic}':
                return ch
        return None

async def setup(bot) -> None:
    await bot.add_cog(Ticket(bot))