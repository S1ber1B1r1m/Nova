# cogs/moderation.py
# Moderasyon, loglama ve auto-mod sistemi

from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import config


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Bir üyeyi sunucudan yasaklar.")
    @app_commands.describe(user="Banlanacak üye", reason="Sebep")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Belirtilmedi"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return
        try:
            await user.ban(reason=reason)
            await interaction.response.send_message(f"{user.mention} banlandı. Sebep: {reason}")
        except Exception as exc:
            await interaction.response.send_message(f"Ban işlemi başarısız: {exc}", ephemeral=True)

    @app_commands.command(name="kick", description="Bir üyeyi sunucudan atar.")
    @app_commands.describe(user="Atılacak üye", reason="Sebep")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Belirtilmedi"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return
        try:
            await user.kick(reason=reason)
            await interaction.response.send_message(f"{user.mention} sunucudan atıldı. Sebep: {reason}")
        except Exception as exc:
            await interaction.response.send_message(f"Kick işlemi başarısız: {exc}", ephemeral=True)

    @app_commands.command(name="temizle", description="Belirtilen sayıda mesaj siler.")
    @app_commands.describe(count="Silinecek mesaj sayısı")
    async def clear(self, interaction: discord.Interaction, count: int):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return
        if count < 1 or count > 100:
            await interaction.response.send_message("1 ile 100 arasında bir sayı gir.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=count)
        await interaction.followup.send(f"{len(deleted)} mesaj silindi.")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None:
            return
        log_channel = discord.utils.get(message.guild.text_channels, name=config.LOG_CHANNEL_NAME)
        if not log_channel:
            return
        embed = discord.Embed(title="Mesaj Silindi", color=discord.Color.dark_red())
        embed.add_field(name="Kullanıcı", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Kanal", value=message.channel.mention, inline=False)
        embed.add_field(name="İçerik", value=message.content[:1000] if message.content else "(Medya/Embed)", inline=False)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.guild is None:
            return
        if before.content == after.content:
            return
        log_channel = discord.utils.get(before.guild.text_channels, name=config.LOG_CHANNEL_NAME)
        if not log_channel:
            return
        embed = discord.Embed(title="Mesaj Düzenlendi", color=discord.Color.orange())
        embed.add_field(name="Kullanıcı", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Kanal", value=before.channel.mention, inline=False)
        embed.add_field(name="Eski", value=before.content[:1000] if before.content else "(Medya/Embed)", inline=False)
        embed.add_field(name="Yeni", value=after.content[:1000] if after.content else "(Medya/Embed)", inline=False)
        await log_channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
