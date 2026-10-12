import csv
import time
from pathlib import Path

from csp_solvers import (
    solve_backtracking,
    solve_mrv_forward_checking,
    solve_min_conflicts,
)


OUTPUT_FILE = Path("benchmark_results.csv")


def run_benchmarks(board_sizes=None):
    """Run and compare the N-Queens solvers."""

    if board_sizes is None:
        board_sizes = [4, 8, 10, 12, 14, 20, 30]

    solvers = [
        solve_backtracking,
        solve_mrv_forward_checking,
        solve_min_conflicts,
    ]

    results = []

    print("=" * 65)
    print("          MINI CHESS AI - CSP BENCHMARKS")
    print("=" * 65)

    for n in board_sizes:
        print(f"\nTesting N = {n}")

        for solver in solvers:

            # Ordinary backtracking can become expensive for larger N.
            # Skip it beyond 14 to avoid excessive runtime.
            if solver == solve_backtracking and n > 14:
                result = {
                    "algorithm": "Backtracking",
                    "n": n,
                    "solution": None,
                    "nodes": 0,
                    "time": 0.0,
                    "solved": False,
                    "status": "Skipped (large search space)",
                }
            else:
                start = time.perf_counter()
                result = solver(n)
                elapsed = time.perf_counter() - start

                result["time"] = elapsed
                result["status"] = (
                    "Success" if result["solved"] else "No solution found"
                )

            results.append(result)

            print(
                f"{result['algorithm']:<25} "
                f"Nodes: {result['nodes']:<8} "
                f"Time: {result['time']:.6f}s "
                f"Status: {result['status']}"
            )

    save_results(results)
    print(f"\nResults saved to: {OUTPUT_FILE.resolve()}")

    return results


def save_results(results):
    """Export benchmark results to a CSV file."""

    columns = [
        "n",
        "algorithm",
        "solved",
        "nodes",
        "time",
        "status",
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for result in results:
            writer.writerow({
                "n": result["n"],
                "algorithm": result["algorithm"],
                "solved": result["solved"],
                "nodes": result["nodes"],
                "time": result["time"],
                "status": result["status"],
            })


if __name__ == "__main__":
    run_benchmarks()