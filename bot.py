import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

# ================= MENU =================
main_menu = ReplyKeyboardMarkup(
    [
        ["📊 Statistika", "➕ Trade qo‘shish"],
        ["⚙️ Settings", "🧮 Hisoblash"],
        ["🗑 Statistika tozalash"]
    ],
    resize_keyboard=True
)

# ================= DATA =================
def get_user_file(user_id):
    return f"user_{user_id}.json"

def load_data(user_id):
    if not os.path.exists(get_user_file(user_id)):
        return {
            "balance": 100,
            "risk": 10,
            "trades": [],
            "state": None,
            "temp": {}
        }
    with open(get_user_file(user_id)) as f:
        return json.load(f)

def save_data(data, user_id):
    with open(get_user_file(user_id), "w") as f:
        json.dump(data, f)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot ishga tushdi!", reply_markup=main_menu)

# ================= STAT =================
async def show_stats(update: Update):
    data = load_data(update.effective_user.id)
    trades = data["trades"]

    total = len(trades)
    wins = len([t for t in trades if t["result"] == "win"])
    losses = total - wins
    pnl = sum([t["pnl"] for t in trades])

    text = f"""
📊 STATISTIKA

💰 Balans: {data['balance']}$
⚠️ Risk: {data['risk']}$

📈 PnL: {pnl}$

Trades: {total}
Win: {wins}
Lose: {losses}
"""
    await update.message.reply_text(text, reply_markup=main_menu)

# ================= MESSAGE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    data = load_data(user_id)

    # MENU
    if text == "📊 Statistika":
        await show_stats(update)
        return

    if text == "🗑 Statistika tozalash":
        data["trades"] = []
        save_data(data, user_id)
        await update.message.reply_text("Tozalandi ✅", reply_markup=main_menu)
        return

    # TRADE
    if text == "➕ Trade qo‘shish":
        data["state"] = "result"
        save_data(data, user_id)
        await update.message.reply_text("Win yoki Lose yoz:")
        return

    if data["state"] == "result":
        data["temp"]["result"] = "win" if "win" in text.lower() else "lose"
        data["state"] = "pnl"
        save_data(data, user_id)
        await update.message.reply_text("PnL yoz (masalan 25):")
        return

    if data["state"] == "pnl":
        pnl = float(text)
        if data["temp"]["result"] == "lose":
            pnl = -abs(pnl)

        data["trades"].append({"result": data["temp"]["result"], "pnl": pnl})
        data["balance"] += pnl

        data["state"] = None
        data["temp"] = {}
        save_data(data, user_id)

        await update.message.reply_text("Trade saqlandi ✅", reply_markup=main_menu)
        return

    # SETTINGS
    if text == "⚙️ Settings":
        data["state"] = "choose_setting"
        save_data(data, user_id)
        await update.message.reply_text("Balans yoki Risk yoz:")
        return

    if data["state"] == "choose_setting":
        if "balans" in text.lower():
            data["state"] = "set_balance"
            await update.message.reply_text("Yangi balans:")
        elif "risk" in text.lower():
            data["state"] = "set_risk"
            await update.message.reply_text("Yangi risk:")
        save_data(data, user_id)
        return

    if data["state"] == "set_balance":
        data["balance"] = float(text)
        data["state"] = None
        save_data(data, user_id)
        await update.message.reply_text("Balans yangilandi ✅", reply_markup=main_menu)
        return

    if data["state"] == "set_risk":
        data["risk"] = float(text)
        data["state"] = None
        save_data(data, user_id)
        await update.message.reply_text("Risk yangilandi ✅", reply_markup=main_menu)
        return

    # HISOBLASH
    if text == "🧮 Hisoblash":
        data["state"] = "calc"
        save_data(data, user_id)
        await update.message.reply_text("Stop % yoz:")
        return

    if data["state"] == "calc":
        stop = float(text)
        lev = round((data["risk"] / data["balance"]) * 100 / stop, 2)
        data["state"] = None
        save_data(data, user_id)

        await update.message.reply_text(
            f"📉 Stop: {stop}%\n⚠️ Risk: {data['risk']}$\n🎯 Leverage: {lev}x",
            reply_markup=main_menu
        )
        return

# ================= RUN =================
def run():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("Bot ishlayapti 🚀")
    app.run_polling()

if __name__ == "__main__":
    run()