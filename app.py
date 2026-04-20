from flask import Flask, request, jsonify, render_template, session, redirect, send_file
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

app = Flask(__name__)
app.secret_key = "123"

USER = "admin"
PASS = "admin123"

MAX_THREADS = 20
TIMEOUT = 8

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USER and request.form["password"] == PASS:
            session["login"] = True
            return redirect("/")
    return render_template("login.html")

def protegido():
    return session.get("login")

# FECHA
def format_fecha(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%d/%m/%Y')
    except:
        return "N/A"

# VERIFICADOR
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
                "estado":"OK",
                "user":user,
                "pass":password,
                "server":base,
                "status":info.get("status"),
                "active":info.get("active_cons"),
                "max":info.get("max_connections"),
                "created":format_fecha(info.get("created_at")),
                "exp":format_fecha(info.get("exp_date")),
                "tz":server.get("timezone"),
                "m3u":url
            }
        else:
            return {"estado":"BAD","user":user}
    except:
        return {"estado":"ERROR","user":"?"}

# HOME
@app.route("/")
def home():
    if not protegido():
        return redirect("/login")
    return render_template("index.html")

# CHECK
@app.route("/check", methods=["POST"])
def check():
    texto = request.json.get("listas","")
    lineas = list(set([l.strip() for l in texto.split("\n") if "get.php" in l]))

    resultados = []
    for l in lineas:
        resultados.append(verificar(l))

    return jsonify(resultados)

# EXPORT
@app.route("/export", methods=["POST"])
def export():
    data = request.json.get("data", [])

    with open("hits.txt","w",encoding="utf-8") as f:
        for x in data:
            if x["estado"]=="OK":
                f.write(f"""╭───✦ HIT
├● 👑 USER : {x['user']}
├● 🔐 PASS : {x['pass']}
├● 📅 EXP : {x['exp']}
├● 🌐 SERVER : {x['server']}
╰───✦

🌐 {x['m3u']}

""")

    return send_file("hits.txt", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
