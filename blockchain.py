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
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def hash_transaction(transaction):
        tx_string = json.dumps(transaction, sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()

    @classmethod
    def compute_merkle_root(cls, transactions):
        if not transactions:
            return "0" * 64

        current_level = [cls.hash_transaction(tx) for tx in transactions]

        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(new_hash)

            current_level = next_level

        return current_level[0]

    @classmethod
    def get_merkle_proof(cls, block, target_transaction):
        transactions = block["transactions"]
        target_hash = cls.hash_transaction(target_transaction)
        current_level = [cls.hash_transaction(tx) for tx in transactions]

        if target_hash not in current_level:
            return None

        target_index = current_level.index(target_hash)
        proof = []

        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            if target_index % 2 == 0:
                sibling_index = target_index + 1
                position = "right"
            else:
                sibling_index = target_index - 1
                position = "left"

            proof.append((current_level[sibling_index], position))

            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(new_hash)

            current_level = next_level
            target_index = target_index // 2

        return proof

    @classmethod
    def verify_merkle_proof(cls, transaction, merkle_proof, merkle_root):
        if merkle_proof is None:
            return False

        current_hash = cls.hash_transaction(transaction)

        for sibling_hash, position in merkle_proof:
            if position == "right":
                combined = current_hash + sibling_hash
            else:
                combined = sibling_hash + current_hash

            current_hash = hashlib.sha256(combined.encode()).hexdigest()

        return current_hash == merkle_root

    @property
    def last_block(self):
        return self.chain[-1]

    def create_genesis_block(self):
        transactions = []
        genesis = {
            "index": 1,
            "timestamp": 0,
            "transactions": [],
            "merkle_root": self.compute_merkle_root(transactions),
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
        reward = {"sender": "0", "recipient": miner_address, "amount": 1}
        block_transactions = [reward] + self.current_transactions

        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": [reward] + self.current_transactions,
            "merkle_root": self.compute_merkle_root(block_transactions),
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
            if block.get("merkle_root") != self.compute_merkle_root(
                block["transactions"]
            ):
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
            if current_block.get("merkle_root") != self.compute_merkle_root(
                current_block["transactions"]
            ):
                return False, i + 1

        return True, None


def print_info(block):
    print(
        f"Blok {block['index']} wydobyty w {time() - start:.8f} s, "
        f"nonce={block['nonce']}"
    )
    print("hash:", bc.hash(block))
    print("merkle_root:", block["merkle_root"])
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
    print("Saldo Michal:", bc.get_balance("Michal"))

    print("\n--- SPRAWDZENIE MERKLE TREE ---")

    recomputed_root = Blockchain.compute_merkle_root(block2["transactions"])
    print(
        "Merkle root zgodny z transakcjami block2:",
        recomputed_root == block2["merkle_root"],
    )

    tx_in_block2 = {"sender": "Alice", "recipient": "Bob", "amount": 1}
    proof = Blockchain.get_merkle_proof(block2, tx_in_block2)
    print("Liczba transakcji w block2:", len(block2["transactions"]))
    print("Liczba hashy w dowodzie Merkle (proof):", len(proof))

    is_valid_tx = Blockchain.verify_merkle_proof(
        tx_in_block2, proof, block2["merkle_root"]
    )
    print("Czy transakcja Alice -> Bob (1) jest w block2?:", is_valid_tx)

    fake_tx = {"sender": "Alice", "recipient": "Bob", "amount": 999}
    is_fake_valid = Blockchain.verify_merkle_proof(
        fake_tx, proof, block2["merkle_root"]
    )
    print("Czy zmieniona transakcja (999) przejdzie weryfikację?:", is_fake_valid)

    tx_from_block3 = {"sender": "Kuba", "recipient": "Jakub", "amount": 0.7}
    proof_wrong_block = Blockchain.get_merkle_proof(block2, tx_from_block3)
    print("Dowód dla transakcji z innego bloku:", proof_wrong_block)
