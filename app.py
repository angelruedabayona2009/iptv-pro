from flask import Flask, render_template, request, jsonify, session, redirect
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.secret_key = "123"

USER = "admin"
PASS = "admin123"

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USER and request.form["password"] == PASS:
            session["login"] = True
            return redirect("/")
    return """
    <form method="post">
    <input name="user" placeholder="user"><br>
    <input name="password" placeholder="pass"><br>
    <button>login</button>
    </form>
    """

@app.route("/")
def index():
    if not session.get("login"):
        return redirect("/login")
    return """
    <h1>IPTV PANEL</h1>
    <form method="post" action="/check">
    <textarea name="listas" style="width:300px;height:150px"></textarea><br>
    <button>Verificar</button>
    </form>
    """

@app.route("/check", methods=["POST"])
def check():
    texto = request.form["listas"]
    return f"<pre>{texto}</pre>"

app.run(host="0.0.0.0", port=5000)
