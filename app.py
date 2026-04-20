from flask import Flask, request, jsonify, render_template, send_file
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

app = Flask(__name__)

MAX_THREADS = 10
TIMEOUT = 10

# ================= FORMATO FECHA =================
def format_fecha(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%d/%m/%Y')
    except:
        return "N/A"

# ================= VERIFICADOR REAL =================
def verificar(url):
    try:
        base = url.split("/get.php")[0]
        user = url.split("username=")[1].split("&")[0]
        password = url.split("password=")[1].split("&")[0]

        api = f"{base}/player_api.php?username={user}&password={password}"

        r = requests.get(api, timeout=TIMEOUT)
        data = r.json()

        info = data.get("user_info", {})
        server = data.get("server_info", {})

        if info.get("auth") == 1:
            return {
                "estado": "OK",
                "user": user,
                "pass": password,
                "server": base,
                "status": info.get("status", "Active"),
                "active": info.get("active_cons", "0"),
                "max": info.get("max_connections", "0"),
                "created": format_fecha(info.get("created_at")),
                "exp": format_fecha(info.get("exp_date")),
                "tz": server.get("timezone", "N/A"),
                "m3u": url
            }
        else:
            return {"estado": "BAD", "user": user}

    except Exception as e:
        return {"estado": "ERROR", "error": str(e)}

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= CHECK =================
@app.route("/check", methods=["POST"])
def check():
    texto = request.json.get("listas", "")
    lineas = list(set([l.strip() for l in texto.split("\n") if "get.php" in l]))

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        resultados = list(executor.map(verificar, lineas))

    return jsonify(resultados)

# ================= EXPORT =================
@app.route("/export", methods=["POST"])
def export():
    data = request.json.get("data", [])

    with open("hits.txt", "w", encoding="utf-8") as f:
        for x in data:
            if x["estado"] == "OK":
                f.write(f"""╭───✦ HIT HUNTER
├● 👑 ᴜꜱᴇʀ : {x['user']}
├● 🔐 ᴩᴀꜱꜱ : {x['pass']}
├● ✅ ꜱᴛᴀᴛᴜꜱ : {x['status']}
├● 📶 ᴀᴄᴛɪᴠᴇ : {x['active']}
├● 📡 ᴍᴀx : {x['max']}
├● ⏰ ᴄʀᴇᴀᴛᴇᴅ : {x['created']}
├● 📅 ᴇxᴘɪʀᴀᴛɪᴏɴ : {x['exp']}
├● 🌐 ꜱᴇʀᴠᴇʀ : {x['server']}
├● 🕰️ ᴛɪᴍᴇᴢᴏɴᴇ : {x['tz']}
├● ⚡ ꜱᴄᴀɴᴛʏᴩᴇ : combo scanner
├● 👤 нιт вʏ : PANEL PRO
╰───✦ 🚀

🌐 ᴍ3ᴜ : {x['m3u']}

""")

    return send_file("hits.txt", as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
