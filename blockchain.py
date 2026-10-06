import hashlib
import json
from time import time


class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = {
            "index": 1,
            "timestamp": 0,
            "transactions": [],
            "nonce": 0,
            "previous_hash": "0" * 64,
        }
        self.chain.append(genesis)

    @staticmethod
    def hash(block):
        # sort_keys=True gwarantuje deterministyczną kolejność pól
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": transactions,
            "nonce": 0,
            "previous_hash": self.hash(self.last_block),
        }
        self.chain.append(block)
        return block

    def is_chain_valid(self, chain):
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            if current_block["previous_hash"] != self.hash(previous_block):
                return False, i + 1

        return True, None

    def repair_as_attacker(self, start):
        for i in range(start + 1, len(self.chain)):
            self.chain[i]["previous_hash"] = self.hash(self.chain[i - 1])


if __name__ == "__main__":
    bc = Blockchain()
    bc.add_block(["Alice -> Bob: 5"])
    bc.add_block(["Bob -> Carol: 2"])
    bc.add_block(["Bob -> Carol: 3"])

    for block in bc.chain:
        print(json.dumps(block, indent=2, ensure_ascii=False))
        print("hash:", Blockchain.hash(block))
        print("-" * 70)
        print()

    bc.chain[1]["transactions"][0] = "Alice -> Bob: 500"
    is_valid, index = bc.is_chain_valid(bc.chain)
    print("1) Chain valid:", is_valid, "index:", index)

    bc.repair_as_attacker(1)
    is_valid, index = bc.is_chain_valid(bc.chain)
    print("2) Chain valid:", is_valid, "index:", index)

    bc.chain[-1]["transactions"][0] = "Bob -> Carol: 3000"
    is_valid, index = bc.is_chain_valid(bc.chain)
    print("3) Chain valid:", is_valid, "index:", index)
