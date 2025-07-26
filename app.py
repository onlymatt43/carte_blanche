
from flask import Flask, request, jsonify, render_template, redirect
import hashlib
import json
import os
from utils import load_tokens, save_tokens, save_code_mapping

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/unlock')
def unlock():
    token = request.args.get("token")
    tokens = load_tokens()
    if token not in tokens:
        return "<h1>Access Denied</h1>", 403

    user_ip = request.remote_addr
    data = tokens[token]
    if data["ip"] and data["ip"] != user_ip:
        return "<h1>IP mismatch</h1>", 403

    return redirect(data["link"])

@app.route('/add_token', methods=['POST'])
def add_token():
    data = request.json
    if data.get('admin_code') != 'SECRET123':
        return jsonify({'error': 'Access denied'}), 403

    token = data.get("token")
    link = data.get("link")
    duration = data.get("duration")
    code = data.get("code")

    if not all([token, link, duration, code]):
        return jsonify({'error': 'Missing fields'}), 400

    user_ip = request.remote_addr
    tokens = load_tokens()
    tokens[token] = {
        "link": link,
        "duration": duration,
        "ip": user_ip
    }
    save_tokens(tokens)
    save_code_mapping(code, token)

    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
