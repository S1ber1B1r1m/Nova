# cogs/entertainment.py
# Eğlence komutları, anketler (görselli) ve çekiliş sistemi (katılımcı kaydı DB ile)

from __future__ import annotations

import io
import os
import random
import time

import discord
import requests
from PIL import Image, ImageDraw, ImageFont
from discord import app_commands
from discord.ext import commands

import config

ASSETS_ROOT = os.path.join(os.path.dirname(__file__), "..", "assets")

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: int, bot: commands.Bot):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.bot = bot

    @discord.ui.button(label="Katıl", style=discord.ButtonStyle.success, custom_id="giveaway_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        # DB'ye ekle (tekrar katılım engellenecek UNIQUE ile)
        conn = getattr(self.bot, "db", None)
        if conn is None:
            await interaction.response.send_message("Veritabanı bağlantısı yok, katılım kaydedilemedi.", ephemeral=True)
            return
        cur = conn.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO giveaway_entries (giveaway_id, user_id) VALUES (?, ?)", (self.giveaway_id, interaction.user.id))
            conn.commit()
            await interaction.response.send_message("Çekilişe katıldın!", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"Katılım sırasında hata: {exc}", ephemeral=True)


class PollView(discord.ui.View):
    def __init__(self, poll_id: int, bot: commands.Bot):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        self.bot = bot

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def vote_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._vote(interaction, "A")

    @discord.ui.button(label="B", style=discord.ButtonStyle.secondary)
    async def vote_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._vote(interaction, "B")

    async def _vote(self, interaction: discord.Interaction, choice: str):
        conn = getattr(self.bot, "db", None)
        if conn is None:
            await interaction.response.send_message("Veritabanı bağlantısı yok.", ephemeral=True)
            return
        cur = conn.cursor()
        try:
            cur.execute("INSERT OR REPLACE INTO poll_votes (poll_id, user_id, choice) VALUES ((?), (?), (?))", (self.poll_id, interaction.user.id, choice))
            conn.commit()
            await interaction.response.send_message(f"Oy verildi: {choice}", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"Oy kaydedilemedi: {exc}", ephemeral=True)


class Entertainment(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="anket", description="Anket oluştur (görsel ve A/B butonları).")
    @app_commands.describe(soru="Anket sorusu", a="A seçeneği", b="B seçeneği")
    async def anket(self, interaction: discord.Interaction, soru: str, a: str, b: str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return
        conn = getattr(self.bot, "db", None)
        cur = conn.cursor() if conn else None
        created_at = int(time.time())
        image_path = os.path.join(ASSETS_ROOT, "poll_template.png")
        # DB kaydı
        if cur:
            cur.execute("INSERT INTO polls (guild_id, channel_id, message_id, question, option_a, option_b, image_path, created_at, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (interaction.guild.id, interaction.channel.id, 0, soru, a, b, image_path if os.path.isfile(image_path) else None, created_at, 1))
            conn.commit()
            poll_id = cur.lastrowid
        else:
            poll_id = int(time.time())

        embed = discord.Embed(title="📊 Yeni Anket", description=soru, color=discord.Color.dark_orange())
        embed.add_field(name="A", value=a, inline=False)
        embed.add_field(name="B", value=b, inline=False)
        if os.path.isfile(image_path):
            file = discord.File(image_path, filename="poll.png")
            embed.set_image(url="attachment://poll.png")
            await interaction.response.send_message(embed=embed, file=file, view=PollView(poll_id, self.bot))
        else:
            await interaction.response.send_message(embed=embed, view=PollView(poll_id, self.bot))

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

    @app_commands.command(name="avatar", description="Kullanıcının avatarını gösterir.")
    @app_commands.describe(kullanici="Avatarı gösterilecek üye")
    async def avatar(self, interaction: discord.Interaction, kullanici: discord.Member | None = None):
        target = kullanici or interaction.user
        embed = discord.Embed(title=f"{target.display_name} - Avatar", color=discord.Color.red())
        embed.set_image(url=target.display_avatar.url)
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
        cur = conn.cursor() if conn else None
        if cur:
            cur.execute("INSERT INTO giveaways (guild_id, channel_id, message_id, prize, ends_at, winners, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (interaction.guild.id, interaction.channel.id, 0, odul, ends_at, kazanan_sayisi, 1))
            conn.commit()
            giveaway_id = cur.lastrowid
        else:
            giveaway_id = int(time.time())

        embed = discord.Embed(title="🎉 Çekiliş Başladı", description=f"Ödül: **{odul}**\nBitiş: <t:{ends_at}:F>", color=discord.Color.red())
        # Eğer assets/giveaway_template.png varsa embed görsel olarak ekle
        image_path = os.path.join(ASSETS_ROOT, "giveaway_template.png")
        view = GiveawayView(giveaway_id, self.bot)
        if os.path.isfile(image_path):
            file = discord.File(image_path, filename="giveaway.png")
            await interaction.response.send_message(embed=embed, file=file, view=view)
            sent = await interaction.original_response()
        else:
            await interaction.response.send_message(embed=embed, view=view)
            sent = await interaction.original_response()

        if cur:
            cur.execute("UPDATE giveaways SET message_id=? WHERE id=?", (sent.id, giveaway_id))
            conn.commit()

        async def wait_and_finish():
            await asyncio.sleep(sure)
            # Katılımcıları DB'den al
            participants = []
            if conn:
                cur2 = conn.cursor()
                cur2.execute("SELECT user_id FROM giveaway_entries WHERE giveaway_id=?", (giveaway_id,))
                rows = cur2.fetchall()
                participants = [interaction.guild.get_member(r[0]) or discord.Object(r[0]) for r in rows]
            # Eğer katılımcı yoksa fallback: sunucudan rastgele değil, iptal et
            if not participants:
                await interaction.followup.send("Çekilişe kimse katılmadı veya katılımcı listesi boş. Kazanan seçilemedi.")
                if conn:
                    cur.execute("UPDATE giveaways SET active=0 WHERE id=?", (giveaway_id,))
                    conn.commit()
                return

            # Filtre: üyeler bot olmamalı
            members = [m for m in participants if isinstance(m, discord.Member) and not m.bot]
            if not members:
                # Eğer DB kayıtlarından guild üyeleri bulunamadı (ör: bot çevrimdışı üyeleri bulamadı), fallback: user ids
                members = [m for m in participants if not getattr(m, 'bot', False)]

            winners = random.sample(members, min(kazanan_sayisi, len(members)))
            mentions = []
            for w in winners:
                if isinstance(w, discord.Member):
                    mentions.append(w.mention)
                else:
                    mentions.append(f"<@{w.id}>")

            await interaction.followup.send(f"🎉 Çekiliş sona erdi! Kazanan(lar): {', '.join(mentions)}")

            # Görsel üretimi (ilk kazanan için örnek)
            try:
                img_bytes = await self.generate_winner_card(winners[0], odul) if hasattr(self, 'generate_winner_card') else None
                if img_bytes:
                    file = discord.File(fp=img_bytes, filename="winner.png")
                    await interaction.channel.send(content=f"Tebrikler {mentions[0]}!", file=file)
            except Exception as e:
                await interaction.channel.send(f"Görsel oluşturulamadı: {e}")

            if conn:
                cur.execute("UPDATE giveaways SET active=0 WHERE id=?", (giveaway_id,))
                conn.commit()

        # create_task
        self.bot.loop.create_task(wait_and_finish())

    async def generate_winner_card(self, member: discord.Member, prize: str) -> io.BytesIO:
        """Pillow ile basit kazanan kartı oluşturur - assets içindeki template varsa onu kullanır."""
        W, H = 1200, 450
        base = Image.new("RGB", (W, H), color=(15, 15, 15))
        draw = ImageDraw.Draw(base)

        # Eğer özel template varsa arka plan olarak kullan
        template_path = os.path.join(ASSETS_ROOT, "giveaway_template.png")
        if os.path.isfile(template_path):
            try:
                tpl = Image.open(template_path).convert("RGBA").resize((W, H))
                base.paste(tpl, (0, 0))
            except Exception:
                pass

        # Kazanan avatarı
        try:
            avatar_url = str(member.display_avatar.with_size(512).with_format("png"))
            resp = requests.get(avatar_url, timeout=20)
            av = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((180, 180))
            mask = Image.new("L", av.size, 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse((0, 0, av.size[0], av.size[1]), fill=255)
            base.paste(av, (60, H//2 - 90), mask)
        except Exception:
            pass

        try:
            font_large = ImageFont.truetype("arial.ttf", 64)
            font_mid = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font_large = ImageFont.load_default()
            font_mid = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.text((280, 60), "ÇEKİLİŞ SONA ERDİ", fill=(255, 255, 255), font=font_mid)
        draw.text((280, 120), prize.upper(), fill=(255, 220, 220), font=font_large)
        draw.text((280, 220), member.display_name if isinstance(member, discord.Member) else str(member), fill=(255, 255, 255), font=font_mid)
        sig = "NOVA UNIVERSE • NOVA MASTER"
        w, h = draw.textsize(sig, font=font_small)
        draw.text((W - w - 40, H - h - 30), sig, fill=(255, 255, 255), font=font_small)
        draw.text((W - 120, 30), "NV", fill=(255, 100, 100), font=font_mid)

        out = io.BytesIO()
        base.save(out, format="PNG")
        out.seek(0)
        return out


async def setup(bot: commands.Bot):
    await bot.add_cog(Entertainment(bot))
