import sys
import chess

from PySide6.QtCore import Qt, QProcess
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFrame,
    QMessageBox,
    QComboBox,
    QDialog,
    QTextEdit,
)

from chess_engine import MiniChessAI
from nqueens_widget import NQueensWidget


class MiniChessApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mini Chess AI | Desktop")
        self.setMinimumSize(1050, 700)
        self.resize(1200, 780)

        self.board = chess.Board()
        self.ai = MiniChessAI(depth=3)
        self.selected_square = None
        self.square_buttons = {}
        self.nqueens_window = None
        self.benchmark_dialog = None
        self.benchmark_process = None

        self.piece_symbols = {
            "K": "♔", "Q": "♕", "R": "♖",
            "B": "♗", "N": "♘", "P": "♙",
            "k": "♚", "q": "♛", "r": "♜",
            "b": "♝", "n": "♞", "p": "♟",
        }

        self.build_ui()
        self.refresh_board()

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # Navigation sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(190)
        sidebar.setObjectName("sidebar")

        side_layout = QVBoxLayout(sidebar)

        title = QLabel("MINI CHESS AI")
        title.setObjectName("brand")
        title.setWordWrap(True)
        side_layout.addWidget(title)

        subtitle = QLabel("INTELLIGENCE LAB")
        subtitle.setObjectName("muted")
        side_layout.addWidget(subtitle)

        side_layout.addSpacing(25)

        navigation = [
            ("♟  Chess Engine", self.show_chess_engine),
            ("♛  AI Analysis", self.show_ai_analysis),
            ("♞  N-Queens CSP", self.open_nqueens),
            ("▥  Benchmarks", self.open_benchmarks),
        ]
        for text, callback in navigation:
            button = QPushButton(text)
            button.setObjectName("navitem")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(42)
            button.clicked.connect(callback)
            side_layout.addWidget(button)

        side_layout.addStretch()

        status = QLabel("● ENGINE READY")
        status.setObjectName("status")
        side_layout.addWidget(status)

        main_layout.addWidget(sidebar)

        # Center: chessboard
        center = QVBoxLayout()

        heading = QLabel("Chess Engine")
        heading.setObjectName("heading")
        center.addWidget(heading)

        self.turn_label = QLabel("White to move")
        self.turn_label.setObjectName("muted")
        center.addWidget(self.turn_label)

        board_frame = QFrame()
        board_frame.setObjectName("boardFrame")

        board_layout = QGridLayout(board_frame)
        board_layout.setSpacing(0)
        board_layout.setContentsMargins(0, 0, 0, 0)

        for row in range(8):
            for col in range(8):
                button = QPushButton()
                button.setMinimumSize(48, 48)
                button.setMaximumSize(80, 80)
                button.setCursor(Qt.CursorShape.PointingHandCursor)

                button.clicked.connect(
                    lambda checked=False, r=row, c=col:
                    self.handle_square_click(r, c)
                )

                self.square_buttons[(row, col)] = button
                board_layout.addWidget(button, row, col)

        center.addWidget(board_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        controls = QHBoxLayout()

        self.ai_button = QPushButton("GET AI MOVE")
        self.ai_button.clicked.connect(self.get_ai_move)
        controls.addWidget(self.ai_button)

        undo_button = QPushButton("UNDO MOVE")
        undo_button.clicked.connect(self.undo_move)
        controls.addWidget(undo_button)

        reset_button = QPushButton("NEW GAME")
        reset_button.clicked.connect(self.reset_game)
        controls.addWidget(reset_button)

        center.addLayout(controls)
        center.addStretch()

        main_layout.addLayout(center, stretch=3)

        # Right: AI statistics
        panel = QFrame()
        panel.setObjectName("analysisPanel")
        panel.setMinimumWidth(230)
        panel.setMaximumWidth(290)

        panel_layout = QVBoxLayout(panel)

        panel_title = QLabel("AI ANALYSIS")
        panel_title.setObjectName("heading")
        panel_layout.addWidget(panel_title)

        panel_layout.addWidget(QLabel("SEARCH DEPTH"))

        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["1", "2", "3", "4"])
        self.depth_combo.setCurrentText("3")
        self.depth_combo.currentTextChanged.connect(self.change_depth)
        panel_layout.addWidget(self.depth_combo)

        self.best_move_label = QLabel("Best move: —")
        self.score_label = QLabel("Evaluation: —")
        self.nodes_label = QLabel("Nodes searched: —")
        self.cutoffs_label = QLabel("Alpha-beta cutoffs: —")
        self.time_label = QLabel("Search time: —")

        for label in [
            self.best_move_label,
            self.score_label,
            self.nodes_label,
            self.cutoffs_label,
            self.time_label,
        ]:
            label.setObjectName("stat")
            label.setWordWrap(True)
            panel_layout.addWidget(label)

        panel_layout.addSpacing(15)

        panel_layout.addWidget(QLabel("PRINCIPAL VARIATION"))

        self.pv_label = QLabel("Waiting for analysis...")
        self.pv_label.setWordWrap(True)
        self.pv_label.setObjectName("muted")
        panel_layout.addWidget(self.pv_label)

        panel_layout.addSpacing(15)

        panel_layout.addWidget(QLabel("MOVE EXPLANATION"))

        self.explanation_label = QLabel(
            "Run the AI to see its move explanation."
        )
        self.explanation_label.setWordWrap(True)
        self.explanation_label.setObjectName("muted")
        panel_layout.addWidget(self.explanation_label)

        panel_layout.addStretch()

        main_layout.addWidget(panel)

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #111318;
                color: #eeeeee;
                font-family: Segoe UI;
                font-size: 13px;
            }

            #sidebar, #analysisPanel {
                background-color: #191c23;
                border: 1px solid #2a2e38;
                border-radius: 12px;
            }

            #brand {
                color: #ff4d5a;
                font-size: 19px;
                font-weight: bold;
            }

            #heading {
                font-size: 21px;
                font-weight: bold;
            }

            #muted {
                color: #a0a6b5;
            }

            QPushButton#navitem {
                text-align: left;
                padding: 12px 8px;
                color: #d4d7df;
                background-color: transparent;
                border: 1px solid transparent;
            }
            QPushButton#navitem:hover {
                background-color: #292e39;
                border: 1px solid #383e4b;
            }

            #status {
                color: #70e0a0;
                font-weight: bold;
                padding: 5px;
            }

            #stat {
                background-color: #222630;
                border-radius: 6px;
                padding: 10px;
                margin-top: 4px;
            }

            QPushButton {
                background-color: #292e39;
                border: 1px solid #383e4b;
                border-radius: 7px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #383e4b;
            }

            #boardFrame {
                background-color: #191c23;
                border: 2px solid #343946;
                border-radius: 4px;
                padding: 4px;
            }

            QComboBox {
                background-color: #222630;
                border: 1px solid #383e4b;
                padding: 8px;
                border-radius: 5px;
            }
        """)


    def show_chess_engine(self):
        """Return focus to the main chessboard."""
        self.setWindowTitle("Mini Chess AI | Chess Engine")
        self.activateWindow()
        self.raise_()

    def show_ai_analysis(self):
        """The analysis panel is already part of the main chess window."""
        self.setWindowTitle("Mini Chess AI | AI Analysis")
        self.activateWindow()
        self.raise_()
        QMessageBox.information(
            self,
            "AI Analysis",
            "AI Analysis is available in the right-hand panel.\n\n"
            "Choose a search depth, then click GET AI MOVE to view the "
            "evaluation, nodes searched, cutoffs, search time, principal "
            "variation, and move explanation."
        )

    def open_nqueens(self):
        """Open the N-Queens CSP visualizer and keep it reusable."""
        if self.nqueens_window is None:
            self.nqueens_window = NQueensWidget()
        self.nqueens_window.show()
        self.nqueens_window.raise_()
        self.nqueens_window.activateWindow()

    def open_benchmarks(self):
        """Run benchmarks.py and show its live output in a dialog."""
        from pathlib import Path

        script = Path(__file__).resolve().with_name("benchmarks.py")
        if not script.exists():
            QMessageBox.warning(
                self, "Benchmarks unavailable",
                "benchmarks.py was not found beside desktop_app.py.\n"
                "Place benchmarks.py in the same project folder and try again."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Mini Chess AI | CSP Benchmarks")
        dialog.resize(760, 480)
        layout = QVBoxLayout(dialog)
        intro = QLabel(
            "Running N-Queens solver comparisons. Results will be saved to "
            "benchmark_results.csv in the project folder."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        output = QTextEdit()
        output.setReadOnly(True)
        layout.addWidget(output)
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        process = QProcess(dialog)
        process.setProgram(sys.executable)
        process.setArguments([str(script)])
        process.setWorkingDirectory(str(script.parent))
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        def append_output():
            data = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
            if data:
                output.moveCursor(output.textCursor().MoveOperation.End)
                output.insertPlainText(data)
                output.ensureCursorVisible()
        process.readyReadStandardOutput.connect(append_output)
        process.finished.connect(
            lambda code, status: output.append(
                f"\nBenchmark process finished (exit code {code})."
            )
        )
        self.benchmark_dialog = dialog
        self.benchmark_process = process
        process.start()
        dialog.show()

    def refresh_board(self):
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                button = self.square_buttons[(row, col)]

                symbol = (
                    self.piece_symbols[piece.symbol()]
                    if piece else ""
                )

                is_light = (row + col) % 2 == 0

                background = (
                    "#e7dfcc" if is_light else "#77966d"
                )

                foreground = (
                    "#ffffff" if piece and piece.color == chess.BLACK
                    else "#111111"
                )

                border = "2px solid #ff4d5a" if (
                    self.selected_square == square
                ) else "none"

                button.setText(symbol)
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {background};
                        color: {foreground};
                        font-size: 34px;
                        border: {border};
                        border-radius: 0px;
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        background-color: #c7b98f;
                    }}
                """)

        if self.board.is_game_over():
            self.turn_label.setText(
                f"Game over: {self.board.result()}"
            )
        else:
            side = "White" if self.board.turn else "Black"
            self.turn_label.setText(f"{side} to move")

    def handle_square_click(self, row, col):
        square = chess.square(col, 7 - row)
        piece = self.board.piece_at(square)

        if self.selected_square is None:
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.refresh_board()
            return

        move = chess.Move(self.selected_square, square)

        # Promote a pawn to a queen automatically.
        moving_piece = self.board.piece_at(self.selected_square)

        if (
            moving_piece
            and moving_piece.piece_type == chess.PAWN
            and chess.square_rank(square) in (0, 7)
        ):
            move = chess.Move(
                self.selected_square,
                square,
                promotion=chess.QUEEN,
            )

        if move in self.board.legal_moves:
            self.board.push(move)

        self.selected_square = None
        self.refresh_board()

    def get_ai_move(self):
        if self.board.is_game_over():
            QMessageBox.information(
                self,
                "Game Over",
                f"The game has ended: {self.board.result()}",
            )
            return

        self.ai_button.setEnabled(False)
        self.ai_button.setText("THINKING...")
        QApplication.processEvents()

        try:
            result = self.ai.best_move(self.board)
            move = result["move"]

            if move is None:
                return

            san_move = self.board.san(move)

            self.best_move_label.setText(
                f"Best move: {san_move}"
            )
            self.score_label.setText(
                f"Evaluation: {result['score']}"
            )
            self.nodes_label.setText(
                f"Nodes searched: {result['nodes']}"
            )
            self.cutoffs_label.setText(
                f"Alpha-beta cutoffs: {result['cutoffs']}"
            )
            self.time_label.setText(
                f"Search time: {result['time']:.4f} s"
            )

            pv = result["principal_variation"]

            self.pv_label.setText(
                " ".join(self.board.variation_san(pv))
                if pv else "Unavailable"
            )

            self.explanation_label.setText(
                self.ai.explain_move(self.board, move)
            )

            self.board.push(move)
            self.refresh_board()

        except Exception as error:
            QMessageBox.critical(
                self,
                "AI Error",
                str(error),
            )

        finally:
            self.ai_button.setEnabled(True)
            self.ai_button.setText("GET AI MOVE")

    def undo_move(self):
        if self.board.move_stack:
            self.board.pop()

            # Undo a human move and the AI's response together
            # when both moves are present.
            if self.board.move_stack:
                self.board.pop()

            self.selected_square = None
            self.refresh_board()

    def reset_game(self):
        self.board.reset()
        self.selected_square = None

        self.best_move_label.setText("Best move: —")
        self.score_label.setText("Evaluation: —")
        self.nodes_label.setText("Nodes searched: —")
        self.cutoffs_label.setText("Alpha-beta cutoffs: —")
        self.time_label.setText("Search time: —")
        self.pv_label.setText("Waiting for analysis...")
        self.explanation_label.setText(
            "Run the AI to see its move explanation."
        )

        self.refresh_board()

    def change_depth(self, value):
        self.ai.depth = int(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MiniChessApp()
    window.show()

    sys.exit(app.exec())