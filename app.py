
from flask import Flask, request, render_template, make_response, redirect
import json, hashlib, time
from datetime import datetime, timedelta

app = Flask(__name__)
TOKEN_FILE = "product_catalog.json"

def load_tokens():
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=4)

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def is_token_valid(token, ip):
    tokens = load_tokens()
    token_hash = hash_token(token)
    record = tokens.get(token_hash)

    if not record: return None
    if "ip" in record and record["ip"] != ip: return None

    if "ip" not in record:
        record["ip"] = ip
        tokens[token_hash] = record
        save_tokens(tokens)

    expires = record.get("expires")
    if expires and time.time() > expires: return None
    return record.get("link")

@app.after_request
def set_secure_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/add_token', methods=['POST'])
def add_token():
    new_data = request.get_json()
    if not new_data:
        return jsonify({"error": "Aucune donnée reçue"}), 400

    try:
        with open('product_catalog.json', 'r+') as f:
            data = json.load(f)
            data.update(new_data)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/unlock")
def unlock():
    token = request.args.get("token", "")
    ip = request.remote_addr
    link = is_token_valid(token, ip)
    if not link:
        return render_template("index.html", error="Invalid or expired token"), 403
    resp = make_response(render_template("unlock.html", link=link))
    resp.set_cookie("auth", hash_token(token), httponly=True, max_age=3600)
    return resp

if __name__ == "__main__":
    app.run(debug=True)
