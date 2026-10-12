import chess
import time

# Piece values in centipawns
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


class MiniChessAI:
    def __init__(self, depth=3):
        self.depth = depth
        self.nodes = 0
        self.cutoffs = 0
        self.transposition_table = {}

    def evaluate(self, board):
        """Evaluate a position from White's perspective."""

        if board.is_checkmate():
            return -100000 if board.turn == chess.WHITE else 100000

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        material = 0

        for piece_type, value in PIECE_VALUES.items():
            material += value * (
                len(board.pieces(piece_type, chess.WHITE))
                - len(board.pieces(piece_type, chess.BLACK))
            )

        # Mobility: compare the number of legal moves for each side.
        # This is an approximation; legal moves are counted on copies.
        mobility = self._mobility_score(board)

        # King safety: penalize exposed kings and reward nearby defenders.
        king_safety = self._king_safety_score(board)

        return material + mobility + king_safety

    def _mobility_score(self, board):
        """Estimate mobility by counting legal moves for both sides."""

        current_moves = board.legal_moves.count()

        other_board = board.copy()
        other_board.turn = not board.turn

        # This is a lightweight approximation, not a full legal-position
        # reconstruction for the opposite side.
        other_moves = other_board.legal_moves.count()

        white_moves = current_moves if board.turn == chess.WHITE else other_moves
        black_moves = other_moves if board.turn == chess.WHITE else current_moves

        return 2 * (white_moves - black_moves)

    def _king_safety_score(self, board):
        """Simple king-safety heuristic."""

        score = 0

        for color, sign in (
            (chess.WHITE, 1),
            (chess.BLACK, -1),
        ):
            king_square = board.king(color)

            if king_square is None:
                continue

            if board.is_attacked_by(not color, king_square):
                score -= sign * 35

            # A small bonus for castling rights.
            if board.has_kingside_castling_rights(color):
                score += sign * 15

            if board.has_queenside_castling_rights(color):
                score += sign * 15

        return score

    def _negamax(self, board, depth, alpha, beta, ply=0):
        """Negamax alpha-beta search returning (score, principal variation)."""

        self.nodes += 1

        if board.is_checkmate():
            return -100000 + ply, []

        if (
            depth == 0
            or board.is_stalemate()
            or board.is_insufficient_material()
            or board.is_fivefold_repetition()
            or board.is_seventyfive_moves()
        ):
            white_score = self.evaluate(board)
            score = white_score if board.turn == chess.WHITE else -white_score
            return score, []

        original_alpha = alpha
        key = (board.fen(), depth)

        cached = self.transposition_table.get(key)
        if cached is not None:
            return cached

        best_score = -float("inf")
        best_line = []

        moves = list(board.legal_moves)

        # Search captures first to improve pruning.
        moves.sort(
            key=lambda move: board.is_capture(move),
            reverse=True,
        )

        for move in moves:
            board.push(move)
            child_score, child_line = self._negamax(
                board,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )
            score = -child_score
            board.pop()

            if score > best_score:
                best_score = score
                best_line = [move] + child_line

            alpha = max(alpha, score)

            if alpha >= beta:
                self.cutoffs += 1
                break

        # Cache only exact results, not cutoff bounds.
        if best_score > original_alpha and best_score < beta:
            self.transposition_table[key] = (best_score, best_line)

        return best_score, best_line

    def best_move(self, board):
        """Return the best move and useful search statistics."""

        self.nodes = 0
        self.cutoffs = 0
        self.transposition_table.clear()

        start_time = time.perf_counter()

        score, line = self._negamax(
            board,
            self.depth,
            -float("inf"),
            float("inf"),
        )

        elapsed = time.perf_counter() - start_time

        move = line[0] if line else None

        return {
            "move": move,
            "score": score,
            "principal_variation": line,
            "nodes": self.nodes,
            "cutoffs": self.cutoffs,
            "depth": self.depth,
            "time": elapsed,
        }

    def explain_move(self, board, move):
        """Provide a basic explanation of a candidate move."""

        if move is None:
            return "No legal move is available."

        piece = board.piece_at(move.from_square)
        piece_name = chess.piece_name(piece.piece_type).capitalize()

        destination_piece = board.piece_at(move.to_square)

        if destination_piece is not None:
            reason = (
                f"The {piece_name.lower()} captures "
                f"the opponent's {chess.piece_name(destination_piece.piece_type)}."
            )
        elif board.gives_check(move):
            reason = f"The {piece_name.lower()} gives check."
        else:
            reason = (
                f"The {piece_name.lower()} moves to improve the evaluated position."
            )

        return (
            f"Selected move: {board.san(move)}. "
            f"{reason} The search evaluates possible continuations "
            f"to the configured depth."
        )


if __name__ == "__main__":
    board = chess.Board()
    ai = MiniChessAI(depth=3)

    print("===== MINI CHESS AI =====")
    print("Board position:")
    print(board)
    print()

    result = ai.best_move(board)
    move = result["move"]

    if move is None:
        print("No legal move available.")
    else:
        print("Best move:", move)
        print("Evaluation:", result["score"])
        print("Search depth:", result["depth"])
        print("Nodes searched:", result["nodes"])
        print("Alpha-beta cutoffs:", result["cutoffs"])
        print(f"Search time: {result['time']:.4f} seconds")

        pv = result["principal_variation"]
        print(
            "Principal variation:",
            " ".join(board.variation_san(pv)) if pv else "Unavailable",
        )

        print("Explanation:", ai.explain_move(board, move))
        print("Move in chess notation:", board.san(move))
