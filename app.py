from flask import Flask, request, jsonify, render_template, session, redirect, send_file
import requests
from concurrent.futures import ThreadPoolExecutor

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def protegido():
    return session.get("login")

# VERIFICADOR
def verificar(url):
    try:
        base = url.split("/get.php")[0]
        user = url.split("username=")[1].split("&")[0]
        password = url.split("password=")[1].split("&")[0]

        api = f"{base}/player_api.php?username={user}&password={password}"
        r = requests.get(api, timeout=TIMEOUT)

        data = r.json()
        user_info = data.get("user_info", {})

        if user_info.get("auth") == 1:
            return {
                "estado": "OK",
                "user": user,
                "pass": password,
                "server": base,
                "exp_date": user_info.get("exp_date")
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

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        results = list(ex.map(verificar, lineas))

    return jsonify(results)

# EXPORT TXT
@app.route("/export", methods=["POST"])
def export():
    data = request.json.get("data", [])

    with open("hits.txt", "w", encoding="utf-8") as f:
        for x in data:
            if x["estado"] == "OK":
                f.write(f"USER: {x['user']} | PASS: {x['pass']} | SERVER: {x['server']}\n")

    return send_file("hits.txt", as_attachment=True)

# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
