import json, hashlib, time
from datetime import datetime, timedelta

from flask_cors import CORS
app = Flask(__name__)
@app.before_request
def enforce_https():
    if request.headers.get("X-Forwarded-Proto", "http") != "https":
        return redirect(request.url.replace("http://", "https://", 1), code=301)
CORS(app)
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

@app.route('/unlock', methods=['GET', 'POST'])
def unlock():
    if request.method == 'POST':
        submitted_token = request.form.get('token', '').strip()
        client_ip = request.remote_addr
        referer = request.headers.get('Referer', '')

        if not submitted_token:
            return render_template('unlock.html', error="Code requis.")

        with open('product_catalog.json', 'r') as f:
            catalog = json.load(f)

        hashed_submitted = hashlib.sha256(submitted_token.encode()).hexdigest()

        for entry in catalog:
            if entry['hashed_token'] == hashed_submitted:
                # Vérifie domaine autorisé (si "url" est présent)
                token_url = entry.get('url')
                if token_url:
                    domain_expected = urlparse(token_url).netloc
                    domain_actual = urlparse(referer).netloc
                    if domain_expected != domain_actual:
                        return render_template('unlock.html', error="Ce site n'est pas autorisé.")

                # Vérifie et enregistre IP
                if 'ip' not in entry:
                    entry['ip'] = client_ip
                    with open('product_catalog.json', 'w') as f:
                        json.dump(catalog, f, indent=2)
                elif entry['ip'] != client_ip:
                    return render_template('unlock.html', error="Ce code est déjà utilisé sur un autre réseau.")

                # Tout est bon : set-cookie et redirect
                response = make_response(redirect('/'))
                duration = entry.get("duration_seconds", 3600)
                response.set_cookie('access_token', submitted_token, max_age=duration, httponly=True)
                return response

        return render_template('unlock.html', error="Code invalide.")
    
    return render_template('unlock.html')

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/purge_expired", methods=["POST"])
def purge_expired():
    data = load_tokens()
    now = time.time()
    updated = {
        k: v for k, v in data.items()
        if v.get("expires", now + 1) > now
    }
    with open("product_catalog.json", "w") as f:
        json.dump(updated, f, indent=2)
    return f"{len(data) - len(updated)} token(s) supprimé(s)", 200