import os
from argparse import ArgumentParser
from functools import wraps
from uuid import uuid4

from flask import Flask, jsonify, request

from blockchain import Blockchain

app = Flask(__name__)
node_identifier = str(uuid4()).replace("-", "")
blockchain = Blockchain()

API_KEY = os.environ.get("NODE_API_KEY", "tajny-klucz-lab3")


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        provided_key = request.headers.get("X-API-Key")
        if not provided_key or provided_key != API_KEY:
            return jsonify({"error": "Brak lub nieprawidłowy nagłówek X-API-Key"}), 401
        return func(*args, **kwargs)

    return wrapper


@app.get("/chain")
def full_chain():
    return jsonify(
        {
            "chain": blockchain.chain,
            "length": len(blockchain.chain),
        }
    ), 200


@app.post("/transactions/new")
def new_transaction():
    if not request.data or not request.data.strip():
        return jsonify({"error": "Treść żądania nie może być pusta"}), 400

    values = request.get_json(silent=True)
    if not isinstance(values, dict):
        return jsonify({"error": "Niepoprawny format JSON"}), 400

    try:
        sender, recipient, amount = blockchain.validate_transaction_payload(values)
        index = blockchain.new_transaction(sender, recipient, amount)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"message": f"Transakcja zostanie dodana do bloku {index}"}), 201


@app.post("/mine")
@require_api_key
def mine():
    block = blockchain.mine(node_identifier)
    return jsonify(
        {
            "message": "Wydobyto nowy blok",
            "block": block,
            "hash": blockchain.hash(block),
        }
    ), 200


@app.get("/transactions/pending")
def pending_transactions():
    return jsonify(
        {
            "pending_transactions": blockchain.current_transactions,
            "count": len(blockchain.current_transactions),
        }
    ), 200


@app.get("/block/<int:index>")
def get_block(index):
    for block in blockchain.chain:
        if block["index"] == index:
            return jsonify({"block": block, "hash": blockchain.hash(block)}), 200

    return jsonify({"error": f"Blok o indeksie {index} nie istnieje"}), 404


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", default=5000, type=int)
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port, debug=False)
