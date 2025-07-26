
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
from utils import load_tokens, save_tokens, save_code_mapping, resolve_token_from_code
import hashlib
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/add_token', methods=['POST'])
def add_token():
    data = request.json
    token = data.get('token')
    duration = data.get('duration')
    link = data.get('link')
    visible_code = data.get('code')

    if not token or not duration or not link:
        return jsonify({'error': 'Missing fields'}), 400

    try:
        duration = int(duration)
    except ValueError:
        return jsonify({'error': 'Duration must be an integer'}), 400

    tokens = load_tokens()
    tokens[token] = {'duration': duration, 'link': link, 'ip': None}
    save_tokens(tokens)

    if visible_code:
        save_code_mapping(visible_code, token)

    return jsonify({token: tokens[token]}), 200


@app.route('/unlock', methods=['GET'])
def unlock():
    token = request.args.get('token')
    if not token:
        return render_template("unlock.html", unlocked=False)

    cookie_token = request.cookies.get("access_token")
    if cookie_token != token:
        return render_template("unlock.html", unlocked=False)

    tokens = load_tokens()
    if token not in tokens:
        return render_template("unlock.html", unlocked=False)

    token_data = tokens[token]
    client_ip = request.remote_addr

    if token_data["ip"] is None:
        token_data["ip"] = client_ip
        save_tokens(tokens)
    elif token_data["ip"] != client_ip:
        return render_template("unlock.html", unlocked=False)

    response = make_response(render_template("unlock.html", unlocked=True, link=token_data["link"]))
    response.set_cookie("access_token", token, max_age=int(token_data["duration"]) * 60, samesite="None", secure=True)
    return response


@app.route('/validate_code', methods=['POST'])
def validate_code():
    data = request.json
    token_from_url = data.get('token')
    code_entered = data.get('code')

    if not token_from_url or not code_entered:
        return jsonify({'error': 'Missing input'}), 400

    resolved_token = resolve_token_from_code(code_entered)
    if not resolved_token or resolved_token != token_from_url:
        return jsonify({'error': 'Invalid code'}), 403

    tokens = load_tokens()
    if resolved_token not in tokens:
        return jsonify({'error': 'Token not found'}), 404

    return jsonify({'link': tokens[resolved_token]['link']}), 200


if __name__ == '__main__':

import os
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)


from flask import redirect, url_for

@app.route('/admin', methods=['GET'])
def admin_panel():
    tokens = load_tokens()
    try:
        with open('token_store.json', 'r') as f:
            code_map = json.load(f)
    except:
        code_map = {}

    # Inverse code_map: token -> code
    inverse_map = {v: k for k, v in code_map.items()}
    return render_template("admin.html", tokens=tokens, codes=inverse_map)


@app.route('/delete_token', methods=['POST'])
def delete_token():
    token = request.form.get("token")
    tokens = load_tokens()
    if token in tokens:
        del tokens[token]
        save_tokens(tokens)

    try:
        with open('token_store.json', 'r') as f:
            code_map = json.load(f)
        # Remove token from values
        code_map = {k: v for k, v in code_map.items() if v != token}
        with open('token_store.json', 'w') as f:
            json.dump(code_map, f, indent=4)
    except:
        pass

    return redirect(url_for("admin_panel"))
