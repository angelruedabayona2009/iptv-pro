from flask import Flask, request, jsonify
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

MAX_THREADS = 20
TIMEOUT = 8

# ================= VERIFICADOR =================
def verificar(url):
    try:
        base = url.split("/get.php")[0]
        user = url.split("username=")[1].split("&")[0]
        password = url.split("password=")[1].split("&")[0]

        api = f"{base}/player_api.php?username={user}&password={password}"
        r = requests.get(api, timeout=TIMEOUT)

        if r.status_code != 200:
            return {"estado":"ERROR","user":user}

        data = r.json()

        if data.get("user_info", {}).get("auth") == 1:
            canales = len(data.get("available_channels", []))
            return {"estado":"OK","user":user,"canales":canales}
        else:
            return {"estado":"BAD","user":user,"canales":0}

    except:
        return {"estado":"ERROR","user":"?"}

# ================= HOME =================
from flask import render_template

@app.route("/")
def home():
    return render_template("index.html")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
