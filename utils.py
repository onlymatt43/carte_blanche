
import json
import os

def load_tokens():
    try:
        with open('product_catalog.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_tokens(tokens):
    with open('product_catalog.json', 'w') as f:
        json.dump(tokens, f, indent=4)

def save_code_mapping(code, token):
    try:
        with open('token_store.json', 'r') as f:
            store = json.load(f)
    except:
        store = {}
    store[code] = token
    with open('token_store.json', 'w') as f:
        json.dump(store, f, indent=4)
