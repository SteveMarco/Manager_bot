import os, subprocess, threading, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8565461662:AAHu_kz0_lgwGhNjYJ5Wi2FJFUtlDcnYDkE"
ADMIN_ID = 8443707949
BOTS_DIR = "bots"

processes = {}

def is_admin(uid):
    return uid == ADMIN_ID

def list_bots():
    return [f[:-3] for f in os.listdir(BOTS_DIR) if f.endswith(".py")]

def start_process(name):
    path = f"{BOTS_DIR}/{name}.py"
    processes[name] = subprocess.Popen(["python", path])
    print(f"[STARTED] {name}")

def stop_process(name):
    proc = processes.get(name)
    if proc:
        proc.terminate()
        del processes[name]
        print(f"[STOPPED] {name}")

def watchdog():
    while True:
        for name, proc in list(processes.items()):
            if proc.poll() is not None:
                print(f"[CRASH] {name} restarting")
                start_process(name)
        time.sleep(10)

def keyboard():
    buttons = []
    for b in list_bots():
        buttons.append([
            InlineKeyboardButton(f"▶️ {b}", callback_data=f"start:{b}"),
            InlineKeyboardButton(f"⏹ {b}", callback_data=f"stop:{b}")
        ])
    buttons.append([InlineKeyboardButton("📊 Status", callback_data="status")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🛠 Mini Hoster Control Panel", reply_markup=keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("start:"):
        name = data.split(":")[1]
        if name not in processes:
            start_process(name)
            await q.edit_message_text(f"✅ {name} started", reply_markup=keyboard())
        else:
            await q.answer("Already running", show_alert=True)

    elif data.startswith("stop:"):
        name = data.split(":")[1]
        stop_process(name)
        await q.edit_message_text(f"🛑 {name} stopped", reply_markup=keyboard())

    elif data == "status":
        msg = "📊 Bot Status\n\n"
        for b in list_bots():
            msg += f"{b}: {'🟢 running' if b in processes else '🔴 stopped'}\n"
        await q.edit_message_text(msg, reply_markup=keyboard())

threading.Thread(target=watchdog, daemon=True).start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("Manager bot running (dynamic bots)...")
app.run_polling()
