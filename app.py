from flask import Flask, request, jsonify, render_template, session, redirect, send_file
import requests
from concurrent.futures import ThreadPoolExecutor
import csv

app = Flask(__name__)
app.secret_key = "123"

USER = "admin"
PASS = "admin123"

MAX_THREADS = 20
TIMEOUT = 8

# ================= LOGIN =================
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

# ================= VERIFICADOR =================
def verificar(url):
    try:
        base = url.split("/get.php")[0]
        user = url.split("username=")[1].split("&")[0]
        password = url.split("password=")[1].split("&")[0]

        api = f"{base}/player_api.php?username={user}&password={password}"
        r = requests.get(api, timeout=TIMEOUT)

        data = r.json()

        if data.get("user_info", {}).get("auth") == 1:
            canales = len(data.get("available_channels", []))
            return {"estado":"OK","user":user,"pass":password,"server":base,"canales":canales}
        else:
            return {"estado":"BAD","user":user}

    except:
        return {"estado":"ERROR","user":"?"}

# ================= HOME =================
@app.route("/")
def home():
    if not protegido():
        return redirect("/login")
    return render_template("index.html")

# ================= CHECK =================
@app.route("/check", methods=["POST"])
def check():
    texto = request.json.get("listas","")
    lineas = texto.split("\n")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        results = list(ex.map(verificar, lineas))

    return jsonify(results)

# ================= EXPORT =================
@app.route("/export", methods=["POST"])
def export():
    data = request.json.get("data", [])

    with open("validas.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["server","user","pass","canales"])

        for x in data:
            if x["estado"] == "OK":
                writer.writerow([x["server"], x["user"], x["pass"], x["canales"]])

    return send_file("validas.csv", as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
