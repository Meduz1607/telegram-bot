import os
import json
import matplotlib.pyplot as plt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

# ================= MENULAR =================
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
def file(user_id):
    return f"user_{user_id}.json"

def load(user_id):
    if not os.path.exists(file(user_id)):
        return {"balance":100,"risk":10,"trades":[],"state":None,"temp":{}}
    with open(file(user_id)) as f:
        return json.load(f)

def save(data,user_id):
    with open(file(user_id),"w") as f:
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
    d = load(update.effective_user.id)
    trades = d["trades"]

    if not trades:
        await update.message.reply_text("❗ Trade yo‘q")
        return

    equity = []
    balance = 0

    for t in trades:
        balance += t["pnl"]
        equity.append(balance)

    # ===== STAT =====
    total = len(trades)
    wins = len([t for t in trades if t["result"] == "win"])
    losses = total - wins
    pnl = sum([t["pnl"] for t in trades])
    winrate = (wins / total * 100) if total > 0 else 0

    biggest_win = max([t["pnl"] for t in trades])
    biggest_loss = min([t["pnl"] for t in trades])

    # ===== MAX DRAWDOWN =====
    peak = equity[0]
    max_dd = 0

    for x in equity:
        if x > peak:
            peak = x
        dd = peak - x
        if dd > max_dd:
            max_dd = dd

    # ===== GRAPH =====
    plt.figure(figsize=(11,5))

    # Line
    plt.plot(equity, linewidth=2)

    # Points
    for i, t in enumerate(trades):
        color = "green" if t["pnl"] > 0 else "red"
        plt.scatter(i, equity[i], color=color)

    # Zero line
    plt.axhline(0, linestyle="--")

    # Title
    plt.title(
        f"📈 Equity Curve | PnL: {pnl}$ | Winrate: {winrate:.1f}%"
    )

    # INFO BOX
    textstr = (
        f"Trades: {total}\n"
        f"Win: {wins} | Lose: {losses}\n"
        f"Max Win: {biggest_win}$\n"
        f"Max Loss: {biggest_loss}$\n"
        f"Max Drawdown: {max_dd}$"
    )

    plt.gcf().text(0.02, 0.5, textstr, fontsize=10)

    plt.xlabel("Trade #")
    plt.ylabel("Balance ($)")
    plt.grid(True)

    plt.tight_layout()
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
        d["temp"]={}
        save(d,uid)
        await update.message.reply_text("Menu",reply_markup=main_menu)
        return

    # ===== STAT =====
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

    # ===== SETTINGS =====
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

        await update.message.reply_text("❗ Tugmadan tanlang")
        return

    if d["state"]=="set_balance":
        try:
            d["balance"]=float(text)
        except:
            await update.message.reply_text("❌ Son yoz")
            return

        d["state"]=None
        save(d,uid)
        await update.message.reply_text("Balans yangilandi ✅",reply_markup=main_menu)
        return

    if d["state"]=="set_risk":
        try:
            d["risk"]=float(text)
        except:
            await update.message.reply_text("❌ Son yoz")
            return

        d["state"]=None
        save(d,uid)
        await update.message.reply_text("Risk yangilandi ✅",reply_markup=main_menu)
        return

    # ===== TRADE =====
    if text=="➕ Trade qo‘shish":
        d["state"]="trade"
        d["temp"]={}
        save(d,uid)
        await update.message.reply_text("Natija:",reply_markup=trade_menu)
        return

    if d["state"]=="trade":
        if text not in ["✅ Win","❌ Lose"]:
            await update.message.reply_text("❗ Tugmadan tanlang")
            return

        d["temp"]["r"]="win" if text=="✅ Win" else "lose"
        d["state"]="pnl"
        save(d,uid)

        await update.message.reply_text("PnL yoz (faqat son):",reply_markup=main_menu)
        return

    if d["state"]=="pnl":
        try:
            pnl=float(text)
        except:
            await update.message.reply_text("❌ Faqat son yoz (masalan: 25)")
            return

        if d["temp"]["r"]=="lose":
            pnl=-abs(pnl)

        d["trades"].append({"result":d["temp"]["r"],"pnl":pnl})
        d["balance"]+=pnl

        d["state"]=None
        d["temp"]={}
        save(d,uid)

        await update.message.reply_text("Saqlandi ✅",reply_markup=main_menu)
        return

    # ===== CALC =====
    if text=="🧮 Hisoblash":
        d["state"]="calc"
        save(d,uid)
        await update.message.reply_text("Stop % yoz:")
        return

    if d["state"]=="calc":
        try:
            stop=float(text)
        except:
            await update.message.reply_text("❌ Son yoz")
            return

        lev=round((d["risk"]/d["balance"])*100/stop,2)

        d["state"]=None
        save(d,uid)

        await update.message.reply_text(
            f"📉 Stop: {stop}%\n⚠️ Risk: {d['risk']}$\n🎯 Leverage: {lev}x",
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