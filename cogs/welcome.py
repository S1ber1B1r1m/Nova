# cogs/welcome.py
# Giriş/Çıkış sistemi - welcome image oluşturma ve kanal ayarı
# Özellikler:
# - /giris-kur ile karşılama kanalı ve marka metni (brand) ayarlanır
# - Yeni üye katıldığında otomatik görsel + mention ile karşılama mesajı gönderir
# - Assets içinde welcome_template.png varsa onu kullanır, yoksa dinamik bir kart üretir

from __future__ import annotations

import io
import os
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

import config

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
if not os.path.isdir(ASSETS_DIR):
    os.makedirs(ASSETS_DIR, exist_ok=True)


class Welcome(commands.Cog):
    """Sunucuya giriş/çıkış bildirimi ve görsel üretme."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def ensure_table(self):
        """DB içinde guild ayarları tablosunu oluşturur (varsa atlar)."""
        conn = getattr(self.bot, "db", None)
        if conn is None:
            return
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel_id INTEGER,
                welcome_brand TEXT,
                welcome_image TEXT
            );
            """
        )
        conn.commit()

    @app_commands.command(name="giris-kur", description="Karşılama kanalını ve marka metnini ayarlar.")
    @app_commands.describe(kanal="Karşılama mesajının gideceği kanal", marka="Kart üzerindeki küçük marka metni (ör: NOVA UNIVERSE)", resim="Assets klasöründeki görsel ismi (opsiyonel)")
    async def setup_welcome(self, interaction: discord.Interaction, kanal: discord.TextChannel, marka: Optional[str] = "NOVA UNIVERSE", resim: Optional[str] = None):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Bu komutu kullanmak için sunucu yöneticisi olmalısın.", ephemeral=True)
            return

        await self.ensure_table()
        conn = getattr(self.bot, "db", None)
        if conn is None:
            await interaction.response.send_message("Veritabanı bağlantısı yok, ayar kaydedilemedi.", ephemeral=True)
            return
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO guild_settings (guild_id, welcome_channel_id, welcome_brand, welcome_image) VALUES (?, ?, ?, ?)",
                    (interaction.guild.id, kanal.id, marka, resim))
        conn.commit()
        await interaction.response.send_message(f"Karşılama kanalı {kanal.mention} olarak ayarlandı. Marka: **{marka}**. Görsel: **{resim or 'varsayılan'}**", ephemeral=True)

    @app_commands.command(name="giris", description="Belirtilen kullanıcı için karşılama mesajı gönderir (test/manual).")
    @app_commands.describe(kullanici="Karşılama gönderilecek kullanıcı (opsiyonel)")
    async def manual_welcome(self, interaction: discord.Interaction, kullanici: Optional[discord.Member] = None):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Bu komutu kullanmak için sunucu yöneticisi olmalısın.", ephemeral=True)
            return

        target = kullanici or interaction.user
        await interaction.response.defer(ephemeral=True)
        await self.send_welcome_card(interaction.guild, target, mention_channel=interaction.channel)
        await interaction.followup.send("Karşılama mesajı gönderildi (test).", ephemeral=True)

    async def send_welcome_card(self, guild: discord.Guild, member: discord.Member, mention_channel: Optional[discord.TextChannel] = None):
        """Veritabanından ayarı alır ve karşılama görselini kanal ve/veya DB ayarına göre gönderir."""
        await self.ensure_table()
        conn = getattr(self.bot, "db", None)
        welcome_chan = None
        brand = "NOVA UNIVERSE"
        image_name = None

        if conn:
            cur = conn.cursor()
            cur.execute("SELECT welcome_channel_id, welcome_brand, welcome_image FROM guild_settings WHERE guild_id=?", (guild.id,))
            row = cur.fetchone()
            if row:
                if row[0]:
                    welcome_chan = guild.get_channel(row[0])
                if row[1]:
                    brand = row[1]
                image_name = row[2]

        # If specific mention_channel provided (manual test), use that; otherwise DB channel
        channel_to_send = mention_channel or welcome_chan
        if channel_to_send is None:
            return

        # Format member count with dot as thousands separator (e.g., 23.956)
        member_count_text = f"{guild.member_count:,}".replace(",", ".")

        # Create image bytes
        img_bytes = await self.generate_welcome_image(member, brand, member_count_text, image_name)

        # Prepare message content: mention user and short text
        content = f"Hoş geldin {member.mention}!"
        file = discord.File(fp=img_bytes, filename="welcome.png")
        await channel_to_send.send(content=content, file=file)

    async def generate_welcome_image(self, member: discord.Member, brand: str, member_count_text: str, image_name: Optional[str]) -> io.BytesIO:
        """Pillow ile karşılama görseli üretir. Eğer assets/welcome_template.png varsa onu arka plan olarak kullanır."""
        W, H = 1200, 420
        base = Image.new("RGB", (W, H), color=(20, 20, 20))
        draw = ImageDraw.Draw(base)

        # Try to use template if provided or default one in assets
        template_path = None
        if image_name:
            template_path = os.path.join(ASSETS_DIR, image_name)
        fallback_template = os.path.join(ASSETS_DIR, "welcome_template.png")
        if template_path and os.path.isfile(template_path):
            try:
                tpl = Image.open(template_path).convert("RGBA").resize((W, H))
                base.paste(tpl, (0, 0))
            except Exception:
                pass
        elif os.path.isfile(fallback_template):
            try:
                tpl = Image.open(fallback_template).convert("RGBA").resize((W, H))
                base.paste(tpl, (0, 0))
            except Exception:
                pass
        else:
            # Draw a red-black gradient background like theme
            for y in range(H):
                r = int(config.THEME_PRIMARY[0] * (1 - y / H) * 0.8) + 10
                g = int(config.THEME_PRIMARY[1] * (1 - y / H) * 0.2)
                b = int(config.THEME_PRIMARY[2] * (1 - y / H) * 0.2)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Avatar: dairesel, solda
        try:
            avatar_url = str(member.display_avatar.with_size(512).with_format("png"))
            import requests
            resp = requests.get(avatar_url, timeout=15)
            av = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((200, 200))
            mask = Image.new("L", av.size, 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse((0, 0, av.size[0], av.size[1]), fill=255)
            # avatar border circle
            border = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(border)
            bdraw.ellipse((0, 0, 220, 220), fill=None, outline=(200, 30, 30), width=8)
            base.paste(border, (40 - 10, H // 2 - 110), border)
            base.paste(av, (60, H // 2 - 100), mask)
        except Exception:
            pass

        # Fonts: try to load system font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 72)
            font_mid = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except Exception:
            font_large = ImageFont.load_default()
            font_mid = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Brand text (küçük üst)
        brand_text = brand.upper()
        draw.text((320, 60), brand_text, fill=(255, 100, 100), font=font_small)

        # Main welcome
        draw.text((320, 110), "HOŞ GELDİN", fill=(255, 255, 255), font=font_large)

        # Member's display name large
        name_text = member.display_name
        draw.text((320, 200), name_text, fill=(255, 240, 240), font=font_mid)

        # Member count line: "Seninle birlikte 23.956 kişiyiz, iyi eğlenceler!"
        count_text = f"Seninle birlikte {member_count_text} kişiyiz, iyi eğlenceler!"
        draw.text((320, 260), count_text, fill=(220, 220, 220), font=font_small)

        # Right-bottom signature
        sig = "NOVA UNIVERSE • NOVA MASTER"
        w, h = draw.textsize(sig, font=font_small)
        draw.text((W - w - 40, H - h - 30), sig, fill=(255, 255, 255), font=font_small)

        # Top-right small logo NV
        draw.text((W - 120, 30), "NV", fill=(255, 90, 90), font=font_mid)

        out = io.BytesIO()
        base.save(out, format="PNG")
        out.seek(0)
        return out

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        try:
            await self.send_welcome_card(member.guild, member)
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
