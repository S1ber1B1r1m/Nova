# cogs/level_economy.py
# XP, seviye, coin ve günlük ödül sistemi.

from __future__ import annotations

import random
import sqlite3
import time

import discord
from discord import app_commands
from discord.ext import commands


class LevelEconomy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.conn: sqlite3.Connection | None = None

    async def cog_load(self):
        self.conn = getattr(self.bot, "db", None)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        conn = getattr(self.bot, "db", None)
        if conn is None:
            return

        cursor = conn.cursor()
        user_id = message.author.id
        guild_id = message.guild.id
        gain = random.randint(5, 20)

        cursor.execute(
            "SELECT xp, level, coins FROM users WHERE user_id=? AND guild_id=?",
            (user_id, guild_id),
        )
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO users (user_id, guild_id, xp, level, coins, total_messages) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, guild_id, gain, 1, 0, 1),
            )
        else:
            xp, level, coins = row
            xp += gain
            total_messages = 1
            cursor.execute(
                "SELECT total_messages FROM users WHERE user_id=? AND guild_id=?",
                (user_id, guild_id),
            )
            current_total = cursor.fetchone()
            if current_total is not None:
                total_messages = current_total[0] + 1
            while xp >= level * 100:
                xp -= level * 100
                level += 1
                await message.channel.send(f"🎉 Tebrikler {message.author.mention}! Seviye atladın. Yeni seviye: {level}")
            cursor.execute(
                "UPDATE users SET xp=?, level=?, total_messages=? WHERE user_id=? AND guild_id=?",
                (xp, level, total_messages, user_id, guild_id),
            )

        conn.commit()

    @app_commands.command(name="profil", description="Kullanıcının profil kartını gösterir.")
    @app_commands.describe(kullanici="Profili gösterilecek üye (opsiyonel)")
    async def profile(self, interaction: discord.Interaction, kullanici: discord.Member | None = None):
        target = kullanici or interaction.user
        conn = getattr(self.bot, "db", None)
        if conn is None:
            await interaction.response.send_message("Veritabanı bağlantısı kurulamadı.", ephemeral=True)
            return

        cursor = conn.cursor()
        cursor.execute(
            "SELECT xp, level, coins FROM users WHERE user_id=? AND guild_id=?",
            (target.id, interaction.guild.id),
        )
        row = cursor.fetchone()
        if row is None:
            await interaction.response.send_message("Bu kullanıcı için profil verisi bulunamadı.", ephemeral=True)
            return

        xp, level, coins = row
        embed = discord.Embed(title=f"{target.display_name} - Profil", color=discord.Color.dark_red())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Seviye", value=str(level), inline=True)
        embed.add_field(name="XP", value=str(xp), inline=True)
        embed.add_field(name="Coin", value=str(coins), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Günlük ödül alır.")
    async def daily(self, interaction: discord.Interaction):
        conn = getattr(self.bot, "db", None)
        if conn is None:
            await interaction.response.send_message("Veritabanı bağlantısı kurulamadı.", ephemeral=True)
            return

        cursor = conn.cursor()
        now = int(time.time())
        cursor.execute(
            "SELECT last_daily, coins FROM users WHERE user_id=? AND guild_id=?",
            (interaction.user.id, interaction.guild.id),
        )
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO users (user_id, guild_id, xp, level, coins, last_daily, total_messages) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (interaction.user.id, interaction.guild.id, 0, 1, 100, now, 0),
            )
            conn.commit()
            await interaction.response.send_message("Günlük ödül alındı: 100 coin", ephemeral=True)
            return

        last_daily, coins = row
        if now - last_daily < 86400:
            await interaction.response.send_message("Günlük ödül zaten alındı. Yakında tekrar deneyebilirsiniz.", ephemeral=True)
            return

        coins += 100
        cursor.execute(
            "UPDATE users SET coins=?, last_daily=? WHERE user_id=? AND guild_id=?",
            (coins, now, interaction.user.id, interaction.guild.id),
        )
        conn.commit()
        await interaction.response.send_message("Günlük ödül alındı: 100 coin", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelEconomy(bot))
