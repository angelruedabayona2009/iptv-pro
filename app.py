from flask import Flask, render_template, request, jsonify, send_file
import requests, time
from datetime import datetime
from db import get_db, init_db
from threading import Thread

# TELEGRAM
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

app = Flask(__name__)
init_db()

# ===== CONFIG ANTI-BAN =====
DELAY = 2
MAX_SCAN = 10

# ⚠️ PON TU NUEVO TOKEN AQUÍ
BOT_TOKEN = "PON_AQUI_TU_TOKEN_NUEVO"

# ===== VERIFICADOR =====
def check_url(url):
    try:
        start = time.time()
        r = requests.get(url, timeout=8)
        t = round(time.time() - start, 2)

        if r.status_code == 200:
            return "ONLINE", t
        return "DOWN", t
    except:
        return "ERROR", 0

# ===== WEB =====
@app.route("/")
def home():
    db = get_db()
    data = db.execute("SELECT * FROM urls").fetchall()
    return render_template("index.html", data=data)

@app.route("/add", methods=["POST"])
def add():
    urls = request.json["urls"].split("\n")
    db = get_db()

    for u in urls:
        u = u.strip()
        if u:
            try:
                db.execute("INSERT INTO urls (url,status) VALUES (?,?)",(u,"NEW"))
            except:
                pass

    db.commit()
    return jsonify({"ok":True})

@app.route("/scan")
def scan():
    db = get_db()
    urls = db.execute("SELECT * FROM urls").fetchall()[:MAX_SCAN]

    for u in urls:
        status, t = check_url(u[1])
        time.sleep(DELAY)

        db.execute("""
        UPDATE urls 
        SET status=?, response_time=?, last_check=? 
        WHERE id=?
        """,(status, t, datetime.now().strftime("%H:%M:%S"), u[0]))

    db.commit()
    return jsonify({"ok":True})

@app.route("/export")
def export():
    db = get_db()
    urls = db.execute("SELECT * FROM urls WHERE status='ONLINE'").fetchall()

    with open("online.txt","w") as f:
        for u in urls:
            f.write(f"{u[1]} | {u[2]} | {u[3]}s\n")

    return send_file("online.txt", as_attachment=True)

# ===== TELEGRAM BOT =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot activo\n\nComandos:\n/add URL\n/scan\n/status")

async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usa: /add https://ejemplo.com")
        return

    url = context.args[0]
    db = get_db()

    try:
        db.execute("INSERT INTO urls (url,status) VALUES (?,?)",(url,"NEW"))
        db.commit()
        await update.message.reply_text("✅ URL añadida")
    except:
        await update.message.reply_text("⚠️ Ya existe")

async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Escaneando...")

    db = get_db()
    urls = db.execute("SELECT * FROM urls").fetchall()[:MAX_SCAN]

    for u in urls:
        status, t = check_url(u[1])
        time.sleep(DELAY)

        db.execute("""
        UPDATE urls 
        SET status=?, response_time=?, last_check=? 
        WHERE id=?
        """,(status, t, datetime.now().strftime("%H:%M:%S"), u[0]))

    db.commit()

    await update.message.reply_text("✅ Escaneo terminado")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    urls = db.execute("SELECT * FROM urls").fetchall()

    msg = "📊 Estado:\n\n"
    for u in urls[:10]:
        msg += f"{u[1]} → {u[2]}\n"

    await update.message.reply_text(msg)

def run_bot():
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("add", add_cmd))
    bot.add_handler(CommandHandler("scan", scan_cmd))
    bot.add_handler(CommandHandler("status", status_cmd))

    bot.run_polling()

# ===== RUN =====
if __name__ == "__main__":
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)
