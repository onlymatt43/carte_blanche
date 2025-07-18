
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
import hashlib
import json
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(BASE_DIR, 'product_catalog.json')

def load_tokens():
    if not os.path.exists(CATALOG_FILE):
        return {}
    with open(CATALOG_FILE, 'r') as f:
        return json.load(f)


TOKEN_STORE_FILE = os.path.join(BASE_DIR, 'token_store.json')

def save_code_mapping(visible_code, hashed_token):
    if not os.path.exists(TOKEN_STORE_FILE):
        store = {}
    else:
        with open(TOKEN_STORE_FILE, 'r') as f:
            try:
                store = json.load(f)
            except:
                store = {}

    store[visible_code] = hashed_token
    with open(TOKEN_STORE_FILE, 'w') as f:
        json.dump(store, f, indent=4)


def save_tokens(tokens):
    if visible_code: save_code_mapping(visible_code, token):
    with open(CATALOG_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)

@app.route('/add_token', methods=['POST'])
def add_token():
    data = request.json
    token = data.get('token')
    visible_code = data.get('code')
    duration = data.get('duration')
    link = data.get('link')
    if not token or not duration or not link:
        return jsonify({'error': 'Missing fields'}), 400
    tokens = load_tokens()
    tokens[token] = {'duration': duration, 'link': link, 'ip': None}
    save_tokens(tokens)
    if visible_code: save_code_mapping(visible_code, token)
    return jsonify({token: tokens[token]}), 200

@app.route('/unlock', methods=['GET'])
def unlock():
    token = request.args.get('token')
    if not token:
        return "Token missing", 400

    # Check if token in cookie matches
    cookie_token = request.cookies.get("access_token")
    if cookie_token != token:
        return "Access denied: token mismatch", 403

    tokens = load_tokens()
    if token not in tokens:
        return "Invalid token", 403
    token_data = tokens[token]
    client_ip = request.remote_addr

    # Check IP binding
    if token_data["ip"] is None:
        token_data["ip"] = client_ip  # First time use → bind IP
        save_tokens(tokens)
    if visible_code: save_code_mapping(visible_code, token)
    elif token_data["ip"] != client_ip:
        return "Access denied: IP mismatch", 403

    # Mark IP address (optional, not enforced here)
    client_ip = request.remote_addr
    token_data['ip'] = client_ip
    save_tokens(tokens)
    if visible_code: save_code_mapping(visible_code, token)

    # Set access cookie
    response = make_response(render_template("unlock.html", link=token_data["link"]))
    response.set_cookie("access_token", token, max_age=int(token_data["duration"]) * 60)
    return response

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/validate_code', methods=['POST'])
def validate_code():
    data = request.json
    token = data.get('token')
    visible_code = data.get('code')  # From URL
    code = data.get('code')    # From input

    if not token or not code:
        return jsonify({'error': 'Missing input'}), 400

    # Compute SHA-256 hash of the entered code
    hashed_code = hashlib.sha256(code.encode()).hexdigest()

    # Compare with the expected token
    if hashed_code != token:
        return jsonify({'error': 'Invalid code'}), 403

    tokens = load_tokens()
    if token not in tokens:
        return jsonify({'error': 'Token not found'}), 404

    client_ip = request.remote_addr
    token_data = tokens[token]

    if token_data["ip"] is None:
        token_data["ip"] = client_ip
        save_tokens(tokens)
    if visible_code: save_code_mapping(visible_code, token)
    elif token_data["ip"] != client_ip:
        return jsonify({'error': 'IP mismatch'}), 403

    response = jsonify({'ok': True})
    response.set_cookie("access_token", token, max_age=int(token_data["duration"]) * 60)
    return response

@app.route('/codes', methods=['GET'])
def get_code_mappings():
    if not os.path.exists(TOKEN_STORE_FILE):
        return jsonify({})
    with open(TOKEN_STORE_FILE, 'r') as f:
        try:
            store = json.load(f)
            return jsonify(store)
        except:
            return jsonify({'error': 'Invalid JSON'}), 500
