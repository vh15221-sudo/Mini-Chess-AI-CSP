import random
import time


def is_safe(queens, row, col):
    """Check whether a queen can be placed at (row, col)."""

    for previous_row in range(row):
        previous_col = queens[previous_row]

        if previous_col == col:
            return False

        if abs(previous_row - row) == abs(previous_col - col):
            return False

    return True


def solve_backtracking(n):
    """Solve N-Queens using ordinary backtracking."""

    queens = [-1] * n
    nodes = 0

    def backtrack(row):
        nonlocal nodes

        if row == n:
            return True

        for col in range(n):
            nodes += 1

            if is_safe(queens, row, col):
                queens[row] = col

                if backtrack(row + 1):
                    return True

                queens[row] = -1

        return False

    start = time.perf_counter()
    solved = backtrack(0)
    elapsed = time.perf_counter() - start

    return {
        "algorithm": "Backtracking",
        "n": n,
        "solution": queens.copy() if solved else None,
        "nodes": nodes,
        "time": elapsed,
        "solved": solved,
    }


def solve_mrv_forward_checking(n):
    """Solve N-Queens using MRV and forward checking."""

    assignments = {}
    domains = {row: set(range(n)) for row in range(n)}
    nodes = 0

    def backtrack():
        nonlocal nodes

        if len(assignments) == n:
            return True

        # Minimum Remaining Values: choose the unassigned row
        # with the smallest remaining domain.
        unassigned = [
            row for row in range(n)
            if row not in assignments
        ]

        row = min(unassigned, key=lambda r: len(domains[r]))

        if not domains[row]:
            return False

        for col in sorted(domains[row]):
            nodes += 1

            if any(
                assignments[r] == col
                or abs(r - row) == abs(assignments[r] - col)
                for r in assignments
            ):
                continue

            assignments[row] = col

            # Save domains so this branch can be undone.
            saved_domains = {
                r: set(domain)
                for r, domain in domains.items()
            }

            consistent = True

            for other_row in range(n):
                if other_row in assignments:
                    continue

                domains[other_row].discard(col)

                diagonal_distance = abs(other_row - row)

                domains[other_row] = {
                    candidate
                    for candidate in domains[other_row]
                    if abs(candidate - col) != diagonal_distance
                }

                if not domains[other_row]:
                    consistent = False
                    break

            if consistent and backtrack():
                return True

            assignments.pop(row)
            domains.clear()
            domains.update(saved_domains)

        return False

    start = time.perf_counter()
    solved = backtrack()
    elapsed = time.perf_counter() - start

    solution = None

    if solved:
        solution = [
            assignments[row]
            for row in range(n)
        ]

    return {
        "algorithm": "MRV + Forward Checking",
        "n": n,
        "solution": solution,
        "nodes": nodes,
        "time": elapsed,
        "solved": solved,
    }


def solve_min_conflicts(n, max_steps=100000, seed=42):
    """Solve N-Queens using the Min-Conflicts heuristic."""

    rng = random.Random(seed)

    # One queen per column; randomly choose a row for each column.
    queens = [rng.randrange(n) for _ in range(n)]
    nodes = 0

    def conflicts(col, row):
        count = 0

        for other_col in range(n):
            if other_col == col:
                continue

            other_row = queens[other_col]

            if other_row == row:
                count += 1

            if abs(other_col - col) == abs(other_row - row):
                count += 1

        return count

    start = time.perf_counter()

    for _ in range(max_steps):
        conflicted = [
            col for col in range(n)
            if conflicts(col, queens[col]) > 0
        ]

        if not conflicted:
            elapsed = time.perf_counter() - start

            return {
                "algorithm": "Min-Conflicts",
                "n": n,
                "solution": queens.copy(),
                "nodes": nodes,
                "time": elapsed,
                "solved": True,
            }

        col = rng.choice(conflicted)

        scores = []

        for row in range(n):
            nodes += 1
            scores.append(conflicts(col, row))

        minimum = min(scores)

        best_rows = [
            row for row, score in enumerate(scores)
            if score == minimum
        ]

        queens[col] = rng.choice(best_rows)

    elapsed = time.perf_counter() - start

    solved = all(
        conflicts(col, queens[col]) == 0
        for col in range(n)
    )

    return {
        "algorithm": "Min-Conflicts",
        "n": n,
        "solution": queens.copy() if solved else None,
        "nodes": nodes,
        "time": elapsed,
        "solved": solved,
    }


def print_board(solution):
    """Display a solved board."""

    if solution is None:
        print("No solution found.")
        return

    n = len(solution)

    for row in range(n):
        print(
            " ".join(
                "Q" if solution[col] == row else "."
                for col in range(n)
            )
        )


if __name__ == "__main__":
    n = 8

    solvers = [
        solve_backtracking,
        solve_mrv_forward_checking,
        solve_min_conflicts,
    ]

    print(f"===== N-QUEENS CSP: N={n} =====\n")

    for solver in solvers:
        result = solver(n)

        print("Algorithm:", result["algorithm"])
        print("Solved:", result["solved"])
        print("Nodes:", result["nodes"])
        print(f"Time: {result['time']:.6f} seconds")

        if result["solved"]:
            print("Solution:", result["solution"])

        print()