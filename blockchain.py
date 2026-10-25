import hashlib
import json
import math
from time import time


class Blockchain:
    def __init__(self, difficulty=4):
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

    def get_balance(self, address):
        if not isinstance(address, str) or not address.strip():
            raise ValueError("Adres musi być niepustym ciągiem znaków")

        balance = 0
        transactions = []
        for block in self.chain:
            transactions.extend(block["transactions"])
        transactions.extend(self.current_transactions)

        for transaction in transactions:
            if transaction["recipient"] == address:
                balance += transaction["amount"]
            if transaction["sender"] == address:
                balance -= transaction["amount"]

        return balance

    def new_transaction(self, sender, recipient, amount):
        if not isinstance(sender, str) or not sender.strip():
            raise ValueError("Nadawca musi być niepustym ciągiem znaków")
        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("Odbiorca musi być niepustym ciągiem znaków")
        if sender == recipient:
            raise ValueError("Nadawca i odbiorca nie mogą być tacy sami")
        if (
            not isinstance(amount, (int, float))
            or isinstance(amount, bool)
            or not math.isfinite(amount)
            or amount <= 0
        ):
            raise ValueError("Kwota musi być dodatnią liczbą")
        if self.get_balance(sender) < amount:
            raise ValueError("Nadawca nie ma wystarczających środków")

        self.current_transactions.append(
            {
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
            }
        )

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
            "previous_hash": self.hash(self.last_block),
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


def print_info(block):
    print(
        f"Blok {block['index']} wydobyty w {time() - start:.8f} s, "
        f"nonce={block['nonce']}"
    )
    print("hash:", bc.hash(block))
    print("Łańcuch poprawny:", bc.valid_chain(bc.chain))
    print()


if __name__ == "__main__":
    bc = Blockchain(difficulty=4)

    start = time()

    block1 = bc.mine(miner_address="Alice")
    print_info(block1)
    bc.new_transaction("Alice", "Bob", 1)
    bc.new_transaction("Bob", "Carol", 0.5)

    block2 = bc.mine(miner_address="Kuba")
    print_info(block2)

    bc.new_transaction("Kuba", "Jakub", 0.7)
    bc.new_transaction("Jakub", "Michal", 0.6)
    block3 = bc.mine(miner_address="Michal")
    print_info(block3)
