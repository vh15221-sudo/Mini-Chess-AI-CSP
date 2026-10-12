import chess


def analyze_position(board):
    """Identify the current chess position's state."""

    result = {
        "turn": "White" if board.turn == chess.WHITE else "Black",
        "in_check": board.is_check(),
        "checkmate": board.is_checkmate(),
        "stalemate": board.is_stalemate(),
        "insufficient_material": board.is_insufficient_material(),
        "legal_moves": board.legal_moves.count(),
        "status": "Normal position",
    }

    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        result["status"] = f"Checkmate. {winner} wins."

    elif board.is_stalemate():
        result["status"] = "Stalemate. The game is drawn."

    elif board.is_insufficient_material():
        result["status"] = "Draw by insufficient material."

    elif board.is_check():
        result["status"] = f"{result['turn']} is in check."

    return result


def explain_position(board):
    """Generate a human-readable explanation."""

    analysis = analyze_position(board)

    print("===== CHESS RULE REASONER =====")

    for key, value in analysis.items():
        print(f"{key.replace('_', ' ').capitalize()}: {value}")

    return analysis


def classify_king_queen_endgame(board):
    """Recognize a basic K+Q versus K material configuration."""

    white_pieces = [
        piece.piece_type
        for piece in board.piece_map().values()
        if piece.color == chess.WHITE
    ]

    black_pieces = [
        piece.piece_type
        for piece in board.piece_map().values()
        if piece.color == chess.BLACK
    ]

    white_kq = (
        len(white_pieces) == 2
        and white_pieces.count(chess.KING) == 1
        and white_pieces.count(chess.QUEEN) == 1
    )

    black_kq = (
        len(black_pieces) == 2
        and black_pieces.count(chess.KING) == 1
        and black_pieces.count(chess.QUEEN) == 1
    )

    white_king_only = white_pieces == [chess.KING]
    black_king_only = black_pieces == [chess.KING]

    if white_kq and black_king_only:
        return "White has King + Queen versus Black's King."

    if black_kq and white_king_only:
        return "Black has King + Queen versus White's King."

    return "Not a basic King + Queen versus King configuration."


if __name__ == "__main__":
    board = chess.Board()

    explain_position(board)
    print()
    print(classify_king_queen_endgame(board))