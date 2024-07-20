import random
from typing import List
from datetime import datetime
import random
import discord
from discord.ext import commands
import discord.ui as ui
from discord import app_commands
from discord.utils import MISSING

from config import Configuration, TicketConfiguration, Topic



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
                    self,
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

    async def close_ticket(self, channel: discord.TextChannel, user: discord.Member):
        if not self.config.roles.get_moderator(channel.guild) in user.roles:
            return PermissionError;
        channel.send(
            f"Ticket closed by {user.mention}"
        )
        #TODO save/export backup of the channel
        await channel.delete()
    
    async def close_ticket_with_reason(self, channel: discord.TextChannel, user: discord.Member, reason: str):
        if not self.config.roles.get_moderator(channel.guild) in user.roles:
            return PermissionError;
        channel.send(
            f"Ticket closed by {user.mention} \nreason: >>{reason}<<"
        )
        #TODO save/export backup of the channel
        await channel.delete()


class TicketChannelView(ui.View):
    def __init__(self, topics: List[Topic], ticket_category: discord.CategoryChannel, ticket_cog, moderator_role = None):
        super().__init__(timeout=None)
        self.ticket_category: discord.CategoryChannel = ticket_category
        self.moderator_role = moderator_role
        self.topics = topics
        self.ticket_cog = ticket_cog


        self.select = ui.Select(
                placeholder ="Make a selection",
                options = Topic.to_discord_options(topics),
                custom_id ="topic_select"
            )
        self.select.callback = self.topic_select_callback
        self.add_item(self.select)
        
    
    async def topic_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        selected_topic = self.select.values[0]
        if (ch := self.already_has_ticket_for(selected_topic, interaction.user.id)) != None:
            await interaction.followup.send(f'You already have a ticket in {ch.mention}', ephemeral=True)
            await self.reset_view(interaction.message)
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
            topic = f'{interaction.user.id}:{selected_topic}',
            overwrites = overwrites,
        )

        #TODO dynamcily create modal for questions(if questions for this topic arent empty-configured)
        for topic in self.topics:
            if topic.value != selected_topic:
                continue
            
            if not topic.questions:
                await self.setup_ticket(channel, {})
                await self.reset_view(interaction.message)
                return

            # Create a modal dialog
            modal = discord.ui.Modal(title="Topic Questions")

            # Add text input fields for each question
            for question in topic.questions:
                modal.add_item(discord.ui.TextInput(
                    label=question,
                    placeholder='Your answer here...',
                    required=True
                ))

            # Define the submit behavior
            async def on_submit(interaction: discord.Interaction):
                answers = {item.label: item.value for item in modal.children}
                await self.setup_ticket(channel, answers)
                await self.reset_view(interaction.message)

            # Set the modal's submit behavior
            modal.on_submit = on_submit

            # Send the modal to the user
            await interaction.send_modal(modal)
            return  # Exit the loop after handling the selected topic
    
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
    
    async def setup_ticket(self, channel: discord.TextChannel, fields: dict):
        embed = discord.Embed(
            description="developed by gotRoasted",
            color=discord.Colour.green()
        )
        for question, anwser in fields:
            embed.add_field(
                name=question,
                value=anwser
            )

        await channel.send(
            embed=embed,
            view=CloseTicketView(self.ticket_cog)
        )
    
class CloseTicketView(ui.View):
    def __init__(self, ticket_cog):
        super().__init__(timeout=None)
        self.ticket_cog: Ticket = ticket_cog

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction.response.defer()
        if await self.ticket_cog.close_ticket(interaction.channel, interaction.user) == PermissionError:
            await interaction.response.send_message("You don't have permissions to close this ticket.", ephemeral=True)
        else:
            await interaction.response.send("Ticket closed!", ephemeral=True)
    
    @discord.ui.button(label="Close With Reason", style=discord.ButtonStyle.danger)
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            CloseTicketWithReason(self.ticket_cog.close_ticket_with_reason)
        )

class CloseTicketWithReason(ui.Modal, title='Close Ticket'):
    reason = ui.TextInput(label='Reason')

    def __init__(self, close_ticket_with_reason) -> None:
        super().__init__()
        self.close_ticket_with_reason = close_ticket_with_reason

    async def on_submit(self, interaction: discord.Interaction):
        interaction.response.defer()
        if await self.close_ticket_with_reason(interaction.channel, interaction.user, self.reason) == PermissionError:
            await interaction.response.send_message("You don't have permissions to close this ticket.", ephemeral=True)
        else:
            await interaction.response.send("Ticket closed!", ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Ticket(bot))