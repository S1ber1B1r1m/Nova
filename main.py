# main.py
# Nova Universe botunun ana çekirdeği.
# Hedef: discord.py 2.x ile çalışır, modüler cog yapısı, SQLite veritabanı ve otomatik yükleme.

import asyncio
import logging
import sqlite3
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nova")

COGS_DIR = Path(__file__).parent / "cogs"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)


def init_db(path: str):
    """SQLite veritabanını başlatır ve gerekli tabloları oluşturur."""
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            guild_id INTEGER,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            coins INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            user_id INTEGER,
            moderator_id INTEGER,
            reason TEXT,
            created_at INTEGER
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            channel_id INTEGER,
            user_id INTEGER,
            type TEXT,
            created_at INTEGER,
            closed INTEGER DEFAULT 0
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            channel_id INTEGER,
            message_id INTEGER,
            prize TEXT,
            ends_at INTEGER,
            winners INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1
        );
        """
    )

    conn.commit()
    return conn


@bot.event
async def on_ready():
    """Bot açıldığında veritabanını kurar ve cogları yükler."""
    bot.db = init_db(config.DATABASE_NAME)
    logger.info(f"{config.BOT_NAME} hazır. Sürüm: {config.VERSION}")

    for file in sorted(COGS_DIR.glob("*.py")):
        module_name = f"cogs.{file.stem}"
        try:
            await bot.load_extension(module_name)
            logger.info(f"Cog yüklendi: {module_name}")
        except Exception as exc:
            logger.exception(f"Cog yüklenemedi: {module_name} - {exc}")

    try:
        await bot.tree.sync()
        logger.info("Slash komutları senkronize edildi.")
    except Exception as exc:
        logger.exception(f"Slash sync hatası: {exc}")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Slash komutunda oluşan hataları kullanıcıya düzgün şekilde gösterir."""
    try:
        await interaction.response.send_message(f"Komut çalıştırılırken hata oluştu: {error}", ephemeral=True)
    except Exception:
        pass
    logger.exception(f"Komut hatası: {error}")


@bot.tree.command(name="kapat", description="Botu kapatır. (Sadece sahip)")
async def shutdown(interaction: discord.Interaction):
    """Bot sahibine özel güvenli kapatma komutu."""
    owner_id = int((os_user_id := os.getenv("OWNER_ID", "0"))) if False else 0
    # Yukarıdaki satır gereksiz; owner kontrolü güvenli bir formda aşağıda yapılacaktır.
    # Önemli: Railway için OWNER_ID env kullanılır.
    owner_id = int(os.getenv("OWNER_ID", "0"))
    if interaction.user.id != owner_id:
        await interaction.response.send_message("Bu komutu sadece bot sahibi kullanabilir.", ephemeral=True)
        return
    await interaction.response.send_message("Bot kapanıyor...", ephemeral=True)
    await bot.close()


if __name__ == "__main__":
    token = config.TOKEN
    if token in (None, "", "PUT_YOUR_TOKEN_HERE"):
        logger.error("DISCORD_TOKEN eksik! config.py içinde veya ortam değişkeninde token tanımla.")
    else:
        bot.run(token)
