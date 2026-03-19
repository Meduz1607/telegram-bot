import os
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ================== TOKEN ==================
TOKEN = os.getenv("BOT_TOKEN")  # Railway-da qo‘shilgan environment variable
if not TOKEN:
    print("❌ BOT_TOKEN environment variable topilmadi!")
    exit(1)

# ================== MENU ==================
main_menu = ReplyKeyboardMarkup(
    [["📊 Statistika", "➕ Trade qo‘shish"], ["⚙️ Settings", "🧮 Hisoblash"]],
    resize_keyboard=True
)

# ================== START HANDLER ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot ishlayapti! 🚀",
        reply_markup=main_menu
    )

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📊 Statistika":
        await update.message.reply_text("📊 Hozir statistika bo‘sh!")
    elif text == "➕ Trade qo‘shish":
        await update.message.reply_text("Trade qo‘shish funksiyasi ishlamoqda!")
    else:
        await update.message.reply_text(f"Siz yozdingiz: {text}")

# ================== AUTO-RESTART / PURGE TASK ==================
async def purge_task(application):
    while True:
        try:
            print("⏰ Purge vaqti tekshirilmoqda...")
            # Agar fayllarni tekshirish yoki xabar yuborish kerak bo‘lsa shu yerga qo‘shish mumkin
            await asyncio.sleep(60)  # 1 daqiqada tekshiradi
        except Exception as e:
            print(f"Purge task xatolik: {e}")
            await asyncio.sleep(10)

# ================== RUN BOT ==================
def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    # post_init da purge task ishga tushadi
    async def post_init(application):
        asyncio.create_task(purge_task(application))

    app.post_init = post_init

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot ishga tushdi... ✅")
    app.run_polling(drop_pending_updates=True)

# ===== AUTO RESTART LOOP =====
if __name__ == "__main__":
    while True:
        try:
            run_bot()
        except Exception as e:
            print(f"Xatolik: {e}")
            print("5 soniyadan keyin qayta ishga tushadi...")
            import time
            time.sleep(5)