import hashlib
import json
from time import time


class Blockchain:
    def __init__(self, difficulty = 4):
        self.chain = []
        self.current_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    @staticmethod
    def hash(block):
        # sort_keys=True gwarantuje deterministyczną kolejność pól
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    @property
    def last_block(self):
        return self.chain[-1]

    def create_genesis_block(self):
        genesis = {
            "index": 1,
            "timestamp": 0,
            "transactions": [],
            "nonce": 0,
            "previous_hash": "0" * 64,
        }
        self.chain.append(genesis)


    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
        })

        return self.last_block["index"] + 1


    def proof_of_work(self, block):
        block["nonce"] = 0
        computed_hash = self.hash(block)

        while not computed_hash.startswith("0" * self.difficulty):
            block["nonce"] += 1
            computed_hash = self.hash(block)
            
        return computed_hash
            
    
    def mine(self, miner_address):
        # Transakcja coinbase (nagroda dla górnika) jako pierwsza w bloku
        reward = {"sender": "0", "recipient": miner_address, "amount": 1}
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": [reward] + self.current_transactions,
            "nonce": 0,
            "previous_hash": self.hash(self.last_block)
        }
        self.proof_of_work(block)
        self.current_transactions = []
        self.chain.append(block)

        return block


    def valid_chain(self, chain):
        if chain[0] != self.chain[0]:
            return False

        for i in range(1, len(chain)):
            previous, block = chain[i - 1], chain[i]
            if block["previous_hash"] != self.hash(previous):
                return False
            if not self.hash(block).startswith("0" * self.difficulty):
                return False

        return True

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
    bc = Blockchain(difficulty=4)
    bc.new_transaction("Alice", "Bob", 5)
    bc.new_transaction("Bob", "Carol", 2)
    
    start = time()
    block = bc.mine(miner_address="miner-1")
    print(f"Blok {block['index']} wydobyty w {time() - start:.2f} s, "f"nonce={block['nonce']}")
    print("hash:", bc.hash(block))
    print("Łańcuch poprawny:", bc.valid_chain(bc.chain))
