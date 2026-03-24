import os
import json
import matplotlib.pyplot as plt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

# ================= MENU =================
main_menu = ReplyKeyboardMarkup(
    [
        ["📊 Statistika", "📈 Grafik"],
        ["➕ Trade qo‘shish"],
        ["⚙️ Settings", "🧮 Hisoblash"],
        ["🗑 Tozalash"]
    ],
    resize_keyboard=True
)

settings_menu = ReplyKeyboardMarkup(
    [
        ["💰 Balans", "⚠️ Risk"],
        ["🔙 Orqaga"]
    ],
    resize_keyboard=True
)

trade_menu = ReplyKeyboardMarkup(
    [
        ["✅ Win", "❌ Lose"],
        ["🔙 Orqaga"]
    ],
    resize_keyboard=True
)

# ================= DATA =================
def get_file(user_id):
    return f"user_{user_id}.json"

def load(user_id):
    if not os.path.exists(get_file(user_id)):
        return {"balance":100,"risk":10,"trades":[],"state":None,"temp":{}}
    with open(get_file(user_id)) as f:
        return json.load(f)

def save(data,user_id):
    with open(get_file(user_id),"w") as f:
        json.dump(data,f)

# ================= START =================
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot tayyor 🚀",reply_markup=main_menu)

# ================= STAT =================
async def stats(update):
    d=load(update.effective_user.id)
    t=d["trades"]

    total=len(t)
    wins=len([x for x in t if x["result"]=="win"])
    pnl=sum([x["pnl"] for x in t])

    text=f"""
📊 STATISTIKA

💰 Balans: {d['balance']}$
⚠️ Risk: {d['risk']}$

📈 PnL: {pnl}$

Trades: {total}
Win: {wins}
Lose: {total-wins}
"""
    await update.message.reply_text(text,reply_markup=main_menu)

# ================= GRAPH =================
async def graph(update):
    d=load(update.effective_user.id)
    t=d["trades"]

    if not t:
        await update.message.reply_text("Trade yo‘q")
        return

    equity=[]
    bal=0
    for x in t:
        bal+=x["pnl"]
        equity.append(bal)

    plt.plot(equity)
    plt.savefig("graph.png")
    plt.close()

    await update.message.reply_photo(open("graph.png","rb"))

# ================= MAIN HANDLER =================
async def handle(update:Update,context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    uid=update.effective_user.id
    d=load(uid)

    # BACK
    if text=="🔙 Orqaga":
        d["state"]=None
        save(d,uid)
        await update.message.reply_text("Menu",reply_markup=main_menu)
        return

    # STAT
    if text=="📊 Statistika":
        await stats(update)
        return

    if text=="📈 Grafik":
        await graph(update)
        return

    if text=="🗑 Tozalash":
        d["trades"]=[]
        save(d,uid)
        await update.message.reply_text("Tozalandi ✅",reply_markup=main_menu)
        return

    # SETTINGS
    if text=="⚙️ Settings":
        d["state"]="settings"
        save(d,uid)
        await update.message.reply_text("Tanlang:",reply_markup=settings_menu)
        return

    if d["state"]=="settings":
        if text=="💰 Balans":
            d["state"]="set_balance"
            save(d,uid)
            await update.message.reply_text("Yangi balans:")
            return
        if text=="⚠️ Risk":
            d["state"]="set_risk"
            save(d,uid)
            await update.message.reply_text("Yangi risk:")
            return

    if d["state"]=="set_balance":
        d["balance"]=float(text)
        d["state"]=None
        save(d,uid)
        await update.message.reply_text("Balans yangilandi ✅",reply_markup=main_menu)
        return

    if d["state"]=="set_risk":
        d["risk"]=float(text)
        d["state"]=None
        save(d,uid)
        await update.message.reply_text("Risk yangilandi ✅",reply_markup=main_menu)
        return

    # TRADE
    if text=="➕ Trade qo‘shish":
        d["state"]="trade"
        save(d,uid)
        await update.message.reply_text("Natija:",reply_markup=trade_menu)
        return

    if d["state"]=="trade":
        if text=="✅ Win":
            d["temp"]["r"]="win"
            d["state"]="pnl"
        elif text=="❌ Lose":
            d["temp"]["r"]="lose"
            d["state"]="pnl"
        save(d,uid)
        await update.message.reply_text("PnL yoz:")
        return

    if d["state"]=="pnl":
        pnl=float(text)
        if d["temp"]["r"]=="lose":
            pnl=-abs(pnl)

        d["trades"].append({"result":d["temp"]["r"],"pnl":pnl})
        d["balance"]+=pnl

        d["state"]=None
        d["temp"]={}
        save(d,uid)

        await update.message.reply_text("Saqlandi ✅",reply_markup=main_menu)
        return

    # CALC
    if text=="🧮 Hisoblash":
        d["state"]="calc"
        save(d,uid)
        await update.message.reply_text("Stop % yoz:")
        return

    if d["state"]=="calc":
        stop=float(text)
        lev=round((d["risk"]/d["balance"])*100/stop,2)

        d["state"]=None
        save(d,uid)

        await update.message.reply_text(
            f"📉 Stop: {stop}%\n⚠️ Risk: {d['risk']}$\n🎯 Lev: {lev}x",
            reply_markup=main_menu
        )
        return

# ================= RUN =================
def run():
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT,handle))

    print("Bot ishlayapti 🚀")
    app.run_polling()

if __name__=="__main__":
    run()