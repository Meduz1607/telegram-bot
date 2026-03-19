import json
import os
import matplotlib.pyplot as plt
import asyncio
import time
import pytz
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@bymeduz"
CHANNEL_LINK = "https://t.me/bymeduz"

# ================== MENU ==================
main_menu = ReplyKeyboardMarkup(
    [
        ["📊 Statistika", "➕ Trade qo‘shish"],
        ["⚙️ Settings", "🧮 Hisoblash"],
        ["🗑 Statistika tozalash"]
    ],
    resize_keyboard=True
)

# ================== DATA ==================
def get_user_file(user_id):
    return f"user_{user_id}.json"

def load_data(user_id):
    user_file = get_user_file(user_id)
    default_data = {
        "static_balance": 100,
        "risk": 10,
        "current_balance": 100,
        "trades": [],
        "state": None,
        "temp": {}
    }
    if not os.path.exists(user_file):
        return default_data
    try:
        with open(user_file, "r") as f:
            data = json.load(f)
        for key in default_data:
            if key not in data:
                data[key] = default_data[key]
        return data
    except:
        return default_data

def save_data(data, user_id):
    user_file = get_user_file(user_id)
    with open(user_file, "w") as f:
        json.dump(data, f, indent=4)

# ================== SUBSCRIPTION ==================
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def ask_subscription(update: Update):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
    ])
    if update.message:
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun kanalga obuna bo‘ling!",
            reply_markup=keyboard
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "❗ Avval kanalga obuna bo‘ling!",
            reply_markup=keyboard
        )

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context):
        await ask_subscription(update)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("BOSHLASH", callback_data="main_menu")]
    ])
    welcome_text = (
        "🤖 PRO TRADING JOURNAL\n\n"
        "Bu bot professional treyderlar uchun.\n\n"
        "📌 Imkoniyatlar:\n"
        "• Stop % yozsangiz — avtomatik Leverage (🧮 Hisoblash)\n"
        "• Trade qo‘shish — Win/Lose + PnL tracking\n"
        "• To‘liq statistika (Balans, PnL, Winrate)\n"
        "• Settings orqali balans va risk boshqaruvi"
    )
    await update.message.reply_text(welcome_text, reply_markup=keyboard)

# ================== LEVERAGE ==================
def calc_leverage(stop_percent, static_balance, risk_amount):
    if stop_percent <= 0 or static_balance <= 0:
        return 0
    risk_percent = (risk_amount / static_balance) * 100
    return round(risk_percent / stop_percent, 2)

# ================== STATISTIKA ==================
async def show_stats(update: Update):
    user_id = update.effective_user.id
    data = load_data(user_id)
    trades = [t for t in data.get("trades", []) if isinstance(t, dict) and "result" in t and "pnl" in t]
total = len(trades)
    wins = len([t for t in trades if t.get("result") == "win"])
    losses = len([t for t in trades if t.get("result") == "lose"])
    pnl = sum([t.get("pnl", 0) for t in trades])
    winrate = (wins / total * 100) if total > 0 else 0

    text = (
        f"📊 STATISTIKA\n\n"
        f"💰 Static balans: {data.get('static_balance', 0)}$\n"
        f"💵 Real balans: {data.get('current_balance', 0):.2f}$\n"
        f"📈 Umumiy PnL: {pnl:.2f}$\n\n"
        f"📊 Trades: {total}\n"
        f"✅ Win: {wins}\n"
        f"❌ Lose: {losses}\n"
        f"🎯 Winrate: {winrate:.1f}%"
    )
    await update.message.reply_text(text, reply_markup=main_menu)

# ================== STATISTIKA TOZALASH ==================
async def reset_stats(update: Update, user_id):
    data = load_data(user_id)
    data["trades"] = []
    data["current_balance"] = data.get("static_balance", 100)
    save_data(data, user_id)
    await update.message.reply_text("✅ Statistika tozalandi!", reply_markup=main_menu)

# ================== GRAPH ==================
async def show_graph(update: Update):
    user_id = update.effective_user.id
    data = load_data(user_id)
    trades = [t for t in data.get("trades", []) if isinstance(t, dict) and "pnl" in t]
    if not trades:
        await update.message.reply_text("Hali trade yo‘q!")
        return

    equity = []
    total = data.get("current_balance", 0)
    for t in trades:
        total += t["pnl"]
        equity.append(total)

    plt.figure(figsize=(8,4))
    plt.plot(equity, marker='o', color='green')
    plt.title("Equity Curve")
    plt.xlabel("Trade #")
    plt.ylabel("Balans ($)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("equity.png")
    plt.close()

    await update.message.reply_photo(open("equity.png", "rb"))

# ================== TRADE LOGIC ==================
async def trade_menu(update: Update):
    user_id = update.effective_user.id
    data = load_data(user_id)
    data["state"] = "await_result"
    save_data(data, user_id)

    keyboard = ReplyKeyboardMarkup(
        [
            ["✅ Win", "❌ Lose"],
            ["🔙 Orqaga"]
        ],
        resize_keyboard=True
    )
    await update.message.reply_text("Trade natijasi qanday?", reply_markup=keyboard)

# ================== CALLBACK ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_sub":
        if await check_subscription(update, context):
            await query.message.reply_text(
                "✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.",
                reply_markup=main_menu
            )
        else:
            await query.message.reply_text("❌ Hali obuna bo‘lmadingiz!", reply_markup=main_menu)
    elif query.data == "main_menu":
        await query.message.reply_text("🚀 Bot foydalanishga tayyor!", reply_markup=main_menu)

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context):
        await ask_subscription(update)
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    data = load_data(user_id)

    if text == "🔙 Orqaga":
        data["state"] = None
        save_data(data, user_id)
        await update.message.reply_text("Bosh menu", reply_markup=main_menu)
        return

    if text == "📊 Statistika":
        await show_stats(update)
        return

    if text == "🗑 Statistika tozalash":
        await reset_stats(update, user_id)
        return
if text == "⚙️ Settings":
        keyboard = ReplyKeyboardMarkup(
            [
                ["💰 Balansni o‘zgartirish"],
                ["⚠️ Riskni o‘zgartirish"],
                ["🔙 Orqaga"]
            ],
            resize_keyboard=True
        )
        text_set = (
            f"⚙️ SETTINGS\n\n"
            f"Static balans: {data.get('static_balance', 0)}$\n"
            f"Real balans: {data.get('current_balance', 0)}$\n"
            f"Risk: {data.get('risk', 0)}$"
        )
        await update.message.reply_text(text_set, reply_markup=keyboard)
        return

    if text == "💰 Balansni o‘zgartirish":
        data["state"] = "set_static_balance"
        save_data(data, user_id)
        await update.message.reply_text("Yangi static balansni kiriting ($):")
        return

    if text == "⚠️ Riskni o‘zgartirish":
        data["state"] = "set_risk"
        save_data(data, user_id)
        await update.message.reply_text("Yangi risk miqdorini kiriting ($):")
        return

    if text == "➕ Trade qo‘shish":
        await trade_menu(update)
        return

    if text in ["✅ Win", "❌ Lose"]:
        data["temp"]["result"] = "win" if text == "✅ Win" else "lose"
        data["state"] = "await_pnl"
        save_data(data, user_id)
        await update.message.reply_text("Qancha + yoki - bo‘ldi? (masalan: 25 yoki 10)")
        return

    if data["state"] == "set_static_balance":
        try:
            bal = float(text)
            data["static_balance"] = bal
            data["state"] = None
            save_data(data, user_id)
            await update.message.reply_text("✅ Static balans yangilandi!", reply_markup=main_menu)
        except:
            await update.message.reply_text("Noto‘g‘ri son kiritildi.")
        return

    if data["state"] == "set_risk":
        try:
            risk = float(text)
            data["risk"] = risk
            data["state"] = None
            save_data(data, user_id)
            await update.message.reply_text("✅ Risk yangilandi!", reply_markup=main_menu)
        except:
            await update.message.reply_text("Noto‘g‘ri son.")
        return

    if data["state"] == "await_pnl":
        try:
            pnl = float(text)
            result = data["temp"].get("result", "win")

            if result == "lose":
                pnl = -abs(pnl)

            data["trades"].append({
                "result": result,
                "pnl": pnl
            })

            data["current_balance"] += pnl
            data["state"] = None
            data["temp"] = {}
            save_data(data, user_id)

            await update.message.reply_text(
                f"📌 Trade saqlandi!\nPnL: {pnl}$",
                reply_markup=main_menu
            )
        except:
            await update.message.reply_text("❌ Iltimos son kiriting (masalan: 10 yoki 25)")
        return

    if text == "🧮 Hisoblash":
        data["state"] = "await_stop_percent"
        save_data(data, user_id)
        await update.message.reply_text("Stop % kiriting (masalan: 0.5):")
        return

    if data["state"] == "await_stop_percent":
        try:
            stop_percent = float(text.replace("%",""))
            lev = calc_leverage(stop_percent, data.get("static_balance",0), data.get("risk",0))
            data["state"] = None
            save_data(data, user_id)
            await update.message.reply_text(
                f"📉 Stop: {stop_percent}%\n"
                f"⚠️ Risk: {data.get('risk',0)}$\n"
                f"🎯 Tavsiya Leverage: {lev}x",
                reply_markup=main_menu
            )
        except:
            await update.message.reply_text("Noto‘g‘ri son. Misol: 0.5 yoki 1.2")
        return

# ================== 24/7 PURGE + AUTO RESTART ==================
async def purge_notifier(application):
    ny_tz = pytz.timezone("America/New_York")
    notify_hours = [1, 3, 5, 6, 8, 9, 11]
while True:
        try:
            now = datetime.now(ny_tz)
            if now.hour in notify_hours and now.minute == 0:
                for file in os.listdir("."):
                    if file.startswith("user_") and file.endswith(".json"):
                        try:
                            user_id = int(file.split("_")[1].split(".")[0])
                            await application.bot.send_message(
                                chat_id=user_id,
                                text="⏰ NY Purge vaqti keldi!"
                            )
                        except:
                            pass
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(10)
        except:
            await asyncio.sleep(30)

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    async def post_init(application):
        asyncio.create_task(purge_notifier(application))

    app.post_init = post_init

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statgraf", show_graph))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot ishga tushdi... 24/7 FREE MODE")
    app.run_polling(drop_pending_updates=True)

# ===== AUTO RESTART LOOP (FREE HOSTING UCHUN) =====
if __name__ == "__main__":
    while True:
        try:
            run_bot()
        except Exception as e:
            print(f"Xatolik: {e}")
            print("Bot 5 soniyadan keyin avtomatik qayta ishga tushadi...")
            time.sleep(5)
