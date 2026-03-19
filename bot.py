import os
from telegram import Bot

# Environment variable’dan token olish
TOKEN = os.getenv("BOT_TOKEN")

# Bot yaratish
bot = Bot(token=TOKEN)

# Ishlayapti degan xabar
print("Bot ishlayapti 🚀")
