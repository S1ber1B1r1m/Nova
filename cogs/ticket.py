# cogs/ticket.py
# Ticket sistemi: panel butonları ile ticket açma, kapatma
# Güncelleme: 'Ban İtiraz' butonu kaldırıldı. Panel artık opsiyonel görsel kullanıyor (assets/ticket_panel.png).

from __future__ import annotations
import time
import os

import discord
from discord.ext import commands
from discord import app_commands

import config

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")

class TicketView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Genel Destek", style=discord.ButtonStyle.primary)
    async def genel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Genel Destek")

    @discord.ui.button(label="Yetkili Başvuru", style=discord.ButtonStyle.secondary)
    async def yetkili(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Yetkili Başvuru")

    # "Ban İtiraz" kaldırıldı per kullanıcı isteği.

    async def create_ticket(self, interaction: discord.Interaction, ttype: str):
        guild = interaction.guild
        cat = discord.utils.get(guild.categories, name=config.SUPPORT_CATEGORY_NAME)
        if cat is None:
            cat = await guild.create_category(config.SUPPORT_CATEGORY_NAME)
        # Kanal adı
        chan_name = f"ticket-{interaction.user.name}".lower()
        # permission overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        # Yetkili rol arama
        yetkili = discord.utils.get(guild.roles, name="Yetkili")
        admin = discord.utils.get(guild.roles, name="Admin")
        if yetkili:
            overwrites[yetkili] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if admin:
            overwrites[admin] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        channel = await guild.create_text_channel(chan_name, category=cat, overwrites=overwrites, reason="Yeni ticket açıldı")
        # DB kaydı
        conn = getattr(self.bot, "db", None)
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO tickets (guild_id, channel_id, user_id, type, created_at) VALUES (?, ?, ?, ?, ?)", (guild.id, channel.id, interaction.user.id, ttype, int(time.time())))
            conn.commit()
        # Ticket mesajı - eğer assets/ticket_panel.png varsa embed görseli olarak kullan
        embed = discord.Embed(title="Yeni Ticket", description=f"Tip: **{ttype}**\n{interaction.user.mention} için açıldı.", color=discord.Color.dark_red())
        panel_path = os.path.join(os.path.dirname(__file__), "..", "assets", "ticket_panel.png")
        if os.path.isfile(panel_path):
            file = discord.File(panel_path, filename="ticket_panel.png")
            embed.set_image(url=f"attachment://ticket_panel.png")
            await channel.send(embed=embed, file=file)
        else:
            await channel.send(embed=embed)

        # Kapatma butonu
        view = discord.ui.View()
        view.add_item(CloseTicketButton(channel.id))
        await channel.send("Ticket kapatma için butona basın.", view=view)
        await interaction.response.send_message(f"Ticket oluşturuldu: {channel.mention}", ephemeral=True)


class CloseTicketButton(discord.ui.Button):
    def __init__(self, channel_id: int):
        super().__init__(label="Ticket Kapat", style=discord.ButtonStyle.red)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel is None:
            await interaction.response.send_message("Kanal bulunamadı veya zaten silinmiş.", ephemeral=True)
            return
        # Basit: yalnızca kanal sahibine veya yetkiliye izin verilebilir. Burada herkes kapatabilir olarak bırakıldı.
        try:
            await channel.delete(reason="Ticket kapatma butonu kullanıldı.")
            await interaction.response.send_message("Ticket kapatıldı.", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"Ticket kapatma hatası: {exc}", ephemeral=True)


class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ticket-panel", description="Ticket paneli gönderir.")
    async def panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return
        embed = discord.Embed(title="Destek Paneli", description="İhtiyacına uygun butona tıkla.", color=discord.Color.dark_red())
        # Eğer panel görseli varsa ekle
        panel_path = os.path.join(os.path.dirname(__file__), "..", "assets", "ticket_panel.png")
        if os.path.isfile(panel_path):
            file = discord.File(panel_path, filename="ticket_panel.png")
            embed.set_image(url=f"attachment://ticket_panel.png")
            await interaction.response.send_message(embed=embed, file=file, view=TicketView(self.bot))
        else:
            await interaction.response.send_message(embed=embed, view=TicketView(self.bot))


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))
