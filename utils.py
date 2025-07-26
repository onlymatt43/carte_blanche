
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(BASE_DIR, 'product_catalog.json')
TOKEN_STORE_FILE = os.path.join(BASE_DIR, 'token_store.json')


def load_tokens():
    if not os.path.exists(CATALOG_FILE):
        return {}
    try:
        with open(CATALOG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return {}


def save_tokens(tokens):
    with open(CATALOG_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)


def save_code_mapping(visible_code, hashed_token):
    store = {}
    if os.path.exists(TOKEN_STORE_FILE):
        try:
            with open(TOKEN_STORE_FILE, 'r') as f:
                store = json.load(f)
        except Exception as e:
            print(f"Error reading token store: {e}")
    store[visible_code] = hashed_token
    with open(TOKEN_STORE_FILE, 'w') as f:
        json.dump(store, f, indent=4)


def resolve_token_from_code(code):
    if not os.path.exists(TOKEN_STORE_FILE):
        return None
    try:
        with open(TOKEN_STORE_FILE, 'r') as f:
            store = json.load(f)
        return store.get(code)
    except Exception as e:
        print(f"Error resolving code: {e}")
        return None
