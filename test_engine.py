import chess
from chess_engine import MiniChessAI


def test_starting_position():
    board = chess.Board()
    ai = MiniChessAI(depth=2)

    result = ai.best_move(board)

    assert result["move"] in board.legal_moves
    assert result["nodes"] > 0
    assert result["depth"] == 2

    print("PASS: AI selects a legal move.")
    print("Best move:", board.san(result["move"]))


def test_principal_variation():
    board = chess.Board()
    ai = MiniChessAI(depth=2)

    result = ai.best_move(board)
    pv = result["principal_variation"]

    assert len(pv) > 0

   
    for move in pv:
        assert move in board.legal_moves
        board.push(move)

    print("PASS: Principal variation contains legal moves.")


def test_alpha_beta_cutoffs():
    board = chess.Board()
    ai = MiniChessAI(depth=3)

    result = ai.best_move(board)

    assert result["cutoffs"] > 0

    print("PASS: Alpha-beta pruning is active.")
    print("Cutoffs:", result["cutoffs"])


if __name__ == "__main__":
    test_starting_position()
    test_principal_variation()
    test_alpha_beta_cutoffs()

    print("\nAll tests passed!")