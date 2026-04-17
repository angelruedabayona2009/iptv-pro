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
@app.route("/")
def home():
    return """
    <h1>🔥 IPTV PANEL PRO</h1>

    <textarea id='listas' style='width:90%;height:200px'></textarea><br><br>

    <button onclick='check()'>Verificar</button>

    <div id='res'></div>

    <script>
    function check(){
        fetch('/check',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                listas:document.getElementById('listas').value
            })
        })
        .then(r=>r.json())
        .then(data=>{
            let html="";
            data.forEach(x=>{
                let color = x.estado=="OK"?"lime":(x.estado=="BAD"?"red":"orange");
                html += `<p style="color:${color}">${x.estado} | ${x.user} | ${x.canales||0}</p>`;
            });
            document.getElementById('res').innerHTML = html;
        });
    }
    </script>
    """

# ================= API =================
@app.route("/check", methods=["POST"])
def check():
    texto = request.json.get("listas","")
    lineas = texto.split("\n")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        results = list(ex.map(verificar, lineas))

    return jsonify(results)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
