# cogs/verification.py
# Kayıt ve doğrulama sistemi - butonlu üye rolü verme

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class VerifyView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="Kayıt Ol", style=discord.ButtonStyle.success)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.user.add_roles(self.role, reason="Kayıt butonuyla üye rolü verildi.")
            await interaction.response.send_message("Başarıyla kaydın tamamlandı! Hoş geldin.", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"Rol verme sırasında hata oluştu: {exc}", ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="dogrulama-kur", description="Doğrulama paneli oluşturur.")
    async def setup_verify(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Bu komutu kullanmak için yetkin yok.", ephemeral=True)
            return

        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="Üye")
        if role is None:
            role = await guild.create_role(name="Üye", reason="Doğrulama için otomatik oluşturuldu.")

        embed = discord.Embed(
            title="Sunucu Kuralları",
            description="Aşağıdaki kuralları okuduktan sonra 'Kayıt Ol' butonuna basarak kaydını tamamlayabilirsin.",
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="1. Saygı", value="Sunucuda saygılı ve kibar ol.", inline=False)
        embed.add_field(name="2. Reklam", value="Reklam ve spam yapma.", inline=False)
        embed.add_field(name="3. Kurallar", value="Kurallara uymayanlar uyarılır.", inline=False)

        view = VerifyView(role)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))
