import csv
import os
from pathlib import Path
from time import perf_counter

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from blockchain import Blockchain

BITCOIN_NETWORK_HASHRATE = 1.07e21  # 1.07 ZH/s
SECONDS_PER_BITCOIN_BLOCK = 600
SECONDS_PER_YEAR = 60 * 60 * 24 * 365.25


def format_number(value):
    return f"{value:,.2f}".replace(",", " ")


def add_initial_balance(blockchain, address, amount):
    blockchain.chain[0]["transactions"].append(
        {"sender": "0", "recipient": address, "amount": amount}
    )


def add_mock_transactions(blockchain):
    blockchain.new_transaction("Bob", "Carol", 2)
    blockchain.new_transaction("Alice", "Bob", 5)


def run_difficulty(output_dir="."):
    output_dir = Path(output_dir)
    results = []

    print("2.2. Badanie wpływu trudności")
    print(
        "| Trudność d | Teoretyczna liczba prób 16^d | "
        "Średnia wartość nonce | Średni czas [s] | Wydajność [H/s] |"
    )
    print("|---:|---:|---:|---:|---:|")

    for difficulty in range(1, 7):
        blocks_to_mine = 2 if difficulty == 6 else 5
        blockchain = Blockchain(difficulty=difficulty)
        add_initial_balance(blockchain, "Alice", 100)
        add_initial_balance(blockchain, "Bob", 100)
        nonces = []
        mining_times = []

        for _ in range(blocks_to_mine):
            add_mock_transactions(blockchain)
            start = perf_counter()
            block = blockchain.mine(miner_address="miner-1")
            elapsed = perf_counter() - start

            nonces.append(block["nonce"])
            mining_times.append(elapsed)

        average_nonce = sum(nonces) / len(nonces)
        average_time = sum(mining_times) / len(mining_times)
        theoretical_attempts = 16**difficulty
        total_hash_attempts = sum(nonce + 1 for nonce in nonces)
        total_time_seconds = sum(mining_times)
        hashes_per_second = total_hash_attempts / total_time_seconds

        result = {
            "difficulty": difficulty,
            "blocks": blocks_to_mine,
            "theoretical_attempts": theoretical_attempts,
            "average_nonce": average_nonce,
            "average_time_seconds": average_time,
            "total_hash_attempts": total_hash_attempts,
            "total_time_seconds": total_time_seconds,
            "hashes_per_second": hashes_per_second,
            "valid_chain": blockchain.valid_chain(blockchain.chain),
        }
        results.append(result)

        print(
            f"| {difficulty} | {theoretical_attempts:,} | "
            f"{average_nonce:.2f} | {average_time:.6f} | {hashes_per_second:.2f} |".replace(
                ",", " "
            )
        )

        if not result["valid_chain"]:
            print(f"UWAGA: łańcuch dla trudności {difficulty} jest niepoprawny")

    save_difficulty_results(results, output_dir)
    estimate_bitcoin_block_time(results)

    return results


def save_difficulty_results(results, output_dir):
    csv_path = output_dir / "difficulty_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nZapisano tabelę: {csv_path}")

    difficulties = [row["difficulty"] for row in results]
    theoretical = [row["theoretical_attempts"] for row in results]
    measured = [row["average_nonce"] + 1 for row in results]

    plt.figure(figsize=(8, 5))
    plt.plot(difficulties, theoretical, marker="o", label="Teoria: 16^d")
    plt.plot(difficulties, measured, marker="o", label="Pomiar: średni nonce + 1")
    plt.yscale("log")
    plt.xlabel("Trudność d")
    plt.ylabel("Liczba prób / nonce + 1 (skala log)")
    plt.title("Wpływ trudności na liczbę prób kopania")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.tight_layout()

    chart_path = output_dir / "difficulty_plot.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
    print(f"Zapisano wykres: {chart_path}")


def estimate_bitcoin_block_time(results):
    own_hashrate = sum(row["total_hash_attempts"] for row in results) / sum(
        row["total_time_seconds"] for row in results
    )
    expected_seconds = (
        SECONDS_PER_BITCOIN_BLOCK * BITCOIN_NETWORK_HASHRATE / own_hashrate
    )
    expected_years = expected_seconds / SECONDS_PER_YEAR

    print("\nSzacowana wydajność komputera:")
    print(f"{format_number(own_hashrate)} H/s")
    print("\nSzacowanie czasu wydobycia jednego bloku Bitcoin:")
    print(f"Hashrate sieci Bitcoin: {BITCOIN_NETWORK_HASHRATE:.2e} H/s")
    print(f"Oczekiwany czas: {expected_years:.2e} lat")


def mine_chain(difficulty, total_blocks=5):
    blockchain = Blockchain(difficulty=difficulty)
    add_initial_balance(blockchain, "Alice", 100)
    add_initial_balance(blockchain, "Bob", 100)

    for block_index in range(2, total_blocks + 1):
        blockchain.new_transaction("Alice", "Bob", block_index)
        blockchain.new_transaction("Bob", "Carol", block_index + 1)
        blockchain.mine(miner_address="miner-1")

    return blockchain


def change_transaction_amount(
    blockchain, block_index=2, transaction_index=1, new_amount=999
):
    block = blockchain.chain[block_index - 1]
    old_amount = block["transactions"][transaction_index]["amount"]
    block["transactions"][transaction_index]["amount"] = new_amount

    return old_amount, new_amount


def remine_from_block(blockchain, start_block_index=2):
    start_position = start_block_index - 1
    reminted_blocks = []
    start = perf_counter()

    for position in range(start_position, len(blockchain.chain)):
        block = blockchain.chain[position]
        block["previous_hash"] = blockchain.hash(blockchain.chain[position - 1])
        blockchain.proof_of_work(block)
        reminted_blocks.append(block["index"])

    elapsed = perf_counter() - start
    return elapsed, reminted_blocks


def run_integrity_attack(total_blocks=5):
    print("2.3. Atak na integralność łańcucha")
    print(
        f"Tworzę łańcuch złożony z {total_blocks} bloków dla trudności 4, "
        "zmieniam transakcję w bloku nr 2 i sprawdzam valid_chain()."
    )

    blockchain = mine_chain(difficulty=4, total_blocks=total_blocks)
    print(
        f"Łańcuch poprawny przed modyfikacją: {blockchain.valid_chain(blockchain.chain)}"
    )

    old_amount, new_amount = change_transaction_amount(blockchain, block_index=2)
    print(f"Zmieniono kwotę transakcji w bloku nr 2: {old_amount} -> {new_amount}")
    print(
        f"Łańcuch poprawny po modyfikacji: {blockchain.valid_chain(blockchain.chain)}"
    )

    print("\nPomiar czasu ataku — ponowne kopanie od bloku nr 2:")
    print(
        "| Trudność | Ponownie kopane bloki | Czas ataku [s] | Łańcuch poprawny po ataku |"
    )
    print("|---:|---:|---:|---:|")

    for difficulty in (4, 5):
        attacked_chain = mine_chain(difficulty=difficulty, total_blocks=total_blocks)
        change_transaction_amount(attacked_chain, block_index=2)
        elapsed, reminted_blocks = remine_from_block(
            attacked_chain, start_block_index=2
        )
        is_valid = attacked_chain.valid_chain(attacked_chain.chain)

        print(
            f"| {difficulty} | {len(reminted_blocks)} "
            f"({', '.join(str(block) for block in reminted_blocks)}) | "
            f"{elapsed:.6f} | {is_valid} |"
        )


def main():
    output_dir = Path(__file__).resolve().parent
    run_difficulty(output_dir=output_dir)
    run_integrity_attack()


if __name__ == "__main__":
    main()
