# Nova Universe

Nova Universe, modüler ve profesyonel bir Discord bot projesidir. Bot, moderasyon, doğrulama, ticket, seviye/ekonomi, eğlence ve çekiliş sistemi içerir.

Özellikler
- Slash komutları (/)
- SQLite veritabanı
- Moderasyon ve auto-mod
- Butonlu kayıt / doğrulama
- Ticket sistemi
- XP / seviye / günlük ödül
- Çekiliş sistemi ve görsel kart üretimi
- Railway uyumlu çalıştırma

Proje yapısı
- config.py
- main.py
- requirements.txt
- Procfile
- README.md
- cogs/
  - moderation.py
  - verification.py
  - level_economy.py
  - ticket.py
  - entertainment.py

Kurulum
1. Python 3.10+ kurulu olmalı.
2. Sanal ortam oluştur:
   - python -m venv .venv
   - Windows: .venv\Scripts\activate
   - macOS/Linux: source .venv/bin/activate
3. Bağımlılıkları yükle:
   - pip install -r requirements.txt
4. Token ayarlama:
   - Railway: DISCORD_TOKEN ortam değişkeni ekle
   - Yerel: config.py içinde TOKEN alanını değiştir
5. Çalıştır:
   - python main.py

Railway
- Yeni bir Railway projesi oluştur.
- Bu repoyu bağla.
- DISCORD_TOKEN ortam değişkenini ekle.
- Procfile otomatik olarak web çalıştırmasını halleder.

Not
- Bot ilk açıldığında gerekli tablo ve cogler otomatik oluşur.
- "nova-log" kanalını ve "🎫 TALEPLER" kategorisini oluşturmayı unutma.
- "Üye", "Yetkili" ve "Admin" rollerini sunucuda oluştur.
