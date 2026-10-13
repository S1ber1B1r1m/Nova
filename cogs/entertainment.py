# cogs/entertainment.py
# Eğlence komutları, duyuru, anket, zar ve basit çekiliş sistemi.

from __future__ import annotations

import io
import random
import time

import discord
import requests
from PIL import Image, ImageDraw, ImageFont
from discord import app_commands
from discord.ext import commands

import config


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Katıl", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Çekilişe katıldın!", ephemeral=True)


class Entertainment(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="google", description="Google arama linki hazırlar.")
    @app_commands.describe(query="Arama metni")
    async def google(self, interaction: discord.Interaction, query: str):
        url = f"https://www.google.com/search?q={requests.utils.requote_uri(query)}"
        await interaction.response.send_message(f"Arama linki: {url}")

    @app_commands.command(name="youtube", description="YouTube arama linki hazırlar.")
    @app_commands.describe(query="Arama metni")
    async def youtube(self, interaction: discord.Interaction, query: str):
        url = f"https://www.youtube.com/results?search_query={requests.utils.requote_uri(query)}"
        await interaction.response.send_message(f"YouTube linki: {url}")

    @app_commands.command(name="duyuru", description="Belirtilen kanala duyuru gönderir.")
    @app_commands.describe(kanal="Duyurunun gideceği kanal", mesaj="Duyuru metni")
    async def duyuru(self, interaction: discord.Interaction, kanal: discord.TextChannel, mesaj: str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return
        await kanal.send(mesaj)
        await interaction.response.send_message(f"Duyuru gönderildi: {kanal.mention}")

    @app_commands.command(name="anket", description="Anket oluşturur.")
    @app_commands.describe(soru="Anket sorusu", a="A şıkkı", b="B şıkkı")
    async def anket(self, interaction: discord.Interaction, soru: str, a: str, b: str):
        embed = discord.Embed(title="📊 Anket", description=soru, color=discord.Color.dark_orange())
        embed.add_field(name="A", value=a, inline=False)
        embed.add_field(name="B", value=b, inline=False)
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🇦")
        await msg.add_reaction("🇧")
        await interaction.response.send_message("Anket oluşturuldu.", ephemeral=True)

    @app_commands.command(name="avatar", description="Kullanıcının avatarını gösterir.")
    @app_commands.describe(kullanici="Avatarı gösterilecek üye")
    async def avatar(self, interaction: discord.Interaction, kullanici: discord.Member | None = None):
        target = kullanici or interaction.user
        embed = discord.Embed(title=f"{target.display_name} - Avatar", color=discord.Color.red())
        embed.set_image(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kullanici-bilgi", description="Kullanıcı bilgilerini gösterir.")
    @app_commands.describe(kullanici="Bilgi gösterilecek üye")
    async def userinfo(self, interaction: discord.Interaction, kullanici: discord.Member | None = None):
        target = kullanici or interaction.user
        embed = discord.Embed(title=f"Kullanıcı: {target.display_name}", color=discord.Color.blurple())
        embed.add_field(name="ID", value=str(target.id), inline=True)
        embed.add_field(name="Katıldı", value=target.joined_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="Roller", value=", ".join(r.name for r in target.roles[1:]) or "Rol yok", inline=False)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="zar-at", description="1 ile 6 arasında zar atar.")
    async def zar(self, interaction: discord.Interaction):
        value = random.randint(1, 6)
        await interaction.response.send_message(f"🎲 Zar atıldı: **{value}**")

    @app_commands.command(name="cekilis-baslat", description="Çekiliş başlatır.")
    @app_commands.describe(sure="Süre (saniye)", odul="Ödül", kazanan_sayisi="Kazanan sayısı")
    async def giveaway(self, interaction: discord.Interaction, sure: int, odul: str, kazanan_sayisi: int = 1):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return

        ends_at = int(time.time()) + sure
        conn = getattr(self.bot, "db", None)
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO giveaways (guild_id, channel_id, message_id, prize, ends_at, winners, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (interaction.guild.id, interaction.channel.id, 0, odul, ends_at, kazanan_sayisi, 1),
            )
            conn.commit()
            giveaway_id = cursor.lastrowid
        else:
            giveaway_id = 0

        embed = discord.Embed(title="🎉 Çekiliş Başladı", description=f"Ödül: **{odul}**\nBitiş: <t:{ends_at}:F>", color=discord.Color.red())
        view = GiveawayView()
        message = await interaction.channel.send(embed=embed, view=view)

        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("UPDATE giveaways SET message_id=? WHERE id=?", (message.id, giveaway_id))
            conn.commit()

        await interaction.response.send_message("Çekiliş başlatıldı.", ephemeral=True)

        async def finish_giveaway():
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=sure))
            members = [m for m in interaction.guild.members if not m.bot]
            if not members:
                await interaction.channel.send("Kazanan seçilemedi.")
                return
            winners = random.sample(members, min(kazanan_sayisi, len(members)))
            winner_msg = "\n".join(f"{w.mention}" for w in winners)
            await interaction.channel.send(f"🎉 Çekiliş sona erdi. Kazanan(lar): {winner_msg}")
            image_bytes = self.generate_winner_card(winners[0], odul)
            await interaction.channel.send(file=discord.File(fp=image_bytes, filename="winner.png"))

        self.bot.loop.create_task(finish_giveaway())

    def generate_winner_card(self, member: discord.Member, prize: str) -> io.BytesIO:
        """Pillow ile basit kazanan kartı üretir."""
        width, height = 1200, 500
        image = Image.new("RGB", (width, height), color=(18, 18, 18))
        draw = ImageDraw.Draw(image)

        # Kırmızı-gri arka plan efekti
        for y in range(height):
            r = max(15, 200 - int((y / height) * 160))
            g = 10
            b = 10
            draw.line((0, y, width, y), fill=(r, g, b))

        try:
            large_font = ImageFont.truetype("arial.ttf", 60)
            mid_font = ImageFont.truetype("arial.ttf", 36)
            small_font = ImageFont.truetype("arial.ttf", 20)
        except OSError:
            large_font = ImageFont.load_default()
            mid_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        draw.text((300, 70), "ÇEKİLİŞ SONA ERDİ", fill=(255, 255, 255), font=mid_font)
        draw.text((300, 120), prize.upper(), fill=(255, 230, 230), font=large_font)
        draw.text((300, 220), member.display_name, fill=(255, 255, 255), font=mid_font)
        draw.text((760, 430), "NOVA UNIVERSE • NOVA MASTER", fill=(255, 255, 255), font=small_font)
        draw.text((1030, 30), "NV", fill=(255, 90, 90), font=mid_font)

        try:
            avatar_url = str(member.display_avatar.with_size(256).with_format("png"))
            response = requests.get(avatar_url, timeout=20)
            avatar = Image.open(io.BytesIO(response.content)).convert("RGBA").resize((170, 170))
            mask = Image.new("L", avatar.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
            image.paste(avatar, (60, 150), mask)
        except Exception:
            pass

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer


async def setup(bot: commands.Bot):
    await bot.add_cog(Entertainment(bot))
