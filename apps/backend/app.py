from flask import Flask, request, jsonify, session, send_from_directory, Response
import requests, json, io, csv, datetime, sqlite3
from config import Settings
from db import init_db, insert_search, last_logs, insert_view, last_views

app = Flask(__name__, static_folder="static", static_url_path="/static")
cfg = Settings()
app.secret_key = cfg.SECRET_KEY

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user":  {"password": "user123",  "role": "user"},
}

def is_logged_in() -> bool:
    return bool(session.get("username"))

# ---------- Static ----------
@app.get("/")
def root():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/app")
def app_page():
    if not is_logged_in():
        return send_from_directory(app.static_folder, "index.html")
    return send_from_directory(app.static_folder, "app.html")

# ---------- Auth ----------
@app.post("/auth/login")
def login():
    data = request.get_json(force=True)
    u = (data.get("username") or "").strip()
    p = data.get("password") or ""
    user = USERS.get(u)
    if not user or user["password"] != p:
        return jsonify({"message":"Invalid credentials"}), 401
    session["username"], session["role"] = u, user["role"]
    return jsonify({"message":"ok", "user":{"username":u,"role":user["role"]}})

@app.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"message":"bye"})

@app.get("/auth/me")
def me():
    if not is_logged_in():
        return jsonify({"authenticated":False}), 401
    return jsonify({"authenticated":True,"user":{"username":session["username"],"role":session["role"]}})

# ---------- Characters ----------
@app.get("/api/characters")
def characters():
    if not is_logged_in():
        return jsonify({"message":"Unauthorized"}), 401

    q = (request.args.get("q") or "").strip()
    page = (request.args.get("page") or "1").strip()
    # <<< clave: solo logear si log=1 (confirmado) >>>
    should_log = (request.args.get("log") == "1")

    params = {}
    if q: params["name"] = q
    if page: params["page"] = page

    try:
        upstream = requests.get(cfg.DRAGON_API_BASE, params=params, timeout=10)
        upstream.raise_for_status()
        data = upstream.json()

        # Normalizar lista
        items = []
        if isinstance(data, dict):
            for k in ("items","characters","results","data"):
                if isinstance(data.get(k), list):
                    items = data[k]; break
        if isinstance(data, list):
            items = data

        if should_log:
            names = []
            for c in (items or [])[:5]:
                names.append(c.get("name") or c.get("character") or c.get("nickname") or "Unknown")
            try:
                insert_search(session["username"], q or "(empty)", len(items), json.dumps(names, ensure_ascii=False))
            except Exception as e:
                print("log error:", e)

        return jsonify({"source":"dragonball-api", "params":params, "data":data})
    except requests.RequestException as e:
        return jsonify({"message":"Upstream error","error":str(e)}), 502

@app.get("/api/characters/<char_id>")
def character_detail(char_id: str):
    if not is_logged_in():
        return jsonify({"message":"Unauthorized"}), 401
    try:
        base = cfg.DRAGON_API_BASE.rstrip("/")
        parent = base.rsplit("/", 1)[0]
        url = f"{parent}/{char_id}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        name = data.get("name") or data.get("character") or data.get("nickname") or f"#{char_id}"
        try:
            insert_view(session["username"], char_id, name)
        except Exception as e:
            print("view log error:", e)
        return jsonify({"data": data})
    except requests.RequestException as e:
        return jsonify({"message":"Upstream error","error":str(e)}), 502

# Si no hay ID confiable, permite registrar vista manual
@app.post("/api/view/log")
def view_log_manual():
    if not is_logged_in():
        return jsonify({"message":"Unauthorized"}), 401
    data = request.get_json(force=True)
    cid = (data.get("id") or "").strip() or None
    name = (data.get("name") or "").strip() or "Unknown"
    try:
        insert_view(session["username"], cid, name)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ---------- Logs ----------
@app.get("/api/search/logs")
def logs():
    if not is_logged_in():
        return jsonify({"message":"Unauthorized"}), 401
    limit = int(request.args.get("limit","20"))
    return jsonify({"logs": last_logs(session["username"], limit)})

@app.get("/api/view/logs")
def view_logs():
    if not is_logged_in():
        return jsonify({"message":"Unauthorized"}), 401
    limit = int(request.args.get("limit","20"))
    return jsonify({"logs": last_views(session["username"], limit)})

@app.get("/api/search/logs/export")
def export_logs():
    if not is_logged_in():
        return jsonify({"message":"Unauthorized"}), 401
    con = sqlite3.connect(cfg.DB_FILE)
    cur = con.execute('select id,username,query,results_count,sample_names,created_at from search_logs order by id')
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['id','username','query','results_count','sample_names','created_at'])
    w.writerows(cur.fetchall())
    con.close()
    filename = f"search_logs_{datetime.datetime.utcnow().date()}.csv"
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
