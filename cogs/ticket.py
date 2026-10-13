# cogs/ticket.py
# Ticket sistemi: butonlu destek paneli ve kategori tabanlı kapatma.

from __future__ import annotations

import time

import discord
from discord import app_commands
from discord.ext import commands

import config


class TicketView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Genel Destek", style=discord.ButtonStyle.primary)
    async def genel_destek(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Genel Destek")

    @discord.ui.button(label="Yetkili Başvuru", style=discord.ButtonStyle.secondary)
    async def yetkili_basvuru(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Yetkili Başvuru")

    @discord.ui.button(label="Ban İtiraz", style=discord.ButtonStyle.danger)
    async def ban_itiraz(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Ban İtiraz")

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=config.SUPPORT_CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(config.SUPPORT_CATEGORY_NAME)

        channel_name = f"ticket-{interaction.user.name}".lower()
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        yetkili = discord.utils.get(guild.roles, name="Yetkili")
        admin = discord.utils.get(guild.roles, name="Admin")
        if yetkili:
            overwrites[yetkili] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        if admin:
            overwrites[admin] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        conn = getattr(self.bot, "db", None)
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tickets (guild_id, channel_id, user_id, type, created_at) VALUES (?, ?, ?, ?, ?)",
                (guild.id, channel.id, interaction.user.id, ticket_type, int(time.time())),
            )
            conn.commit()

        embed = discord.Embed(title="Ticket Oluşturuldu", description=f"Bu ticket tipi: **{ticket_type}**", color=discord.Color.blurple())
        embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=False)
        close_button = CloseTicketButton(channel)
        view = discord.ui.View()
        view.add_item(close_button)
        await channel.send(content=f"{interaction.user.mention} ticket açıldı.", embed=embed, view=view)
        await interaction.response.send_message(f"Ticket başarıyla oluşturuldu: {channel.mention}", ephemeral=True)


class CloseTicketButton(discord.ui.Button):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(label="Ticket Kapat", style=discord.ButtonStyle.red)
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != interaction.user:
            await interaction.response.send_message("Bu butonu sadece ticket sahibi kullanabilir.", ephemeral=True)
            return
        await self.channel.delete(reason="Ticket kapatma butonu kullanıldı.")
        await interaction.response.send_message("Ticket kapatıldı.", ephemeral=True)


class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ticket-panel", description="Ticket paneli gönderir.")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return

        embed = discord.Embed(title="Destek Paneli", description="Aşağıdaki seçeneklerden birini seçerek ticket açabilirsin.", color=discord.Color.dark_red())
        view = TicketView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))
