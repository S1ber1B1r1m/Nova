# config.py
# Nova Universe - temel yapılandırma dosyası
# Railway/hosting ortamlarında DISCORD_TOKEN kullanılır.

import os

TOKEN = os.getenv("DISCORD_TOKEN", "PUT_YOUR_TOKEN_HERE")
BOT_NAME = "Nova Universe"
OWNER_NAME = "Nova Master"
VERSION = "1.0.0"
DATABASE_NAME = "database.db"
LOG_CHANNEL_NAME = "nova-log"
SUPPORT_CATEGORY_NAME = "🎫 TALEPLER"

# Temel tema renkleri için kullanılır.
THEME_PRIMARY = (200, 20, 20)
THEME_SECONDARY = (15, 15, 15)
