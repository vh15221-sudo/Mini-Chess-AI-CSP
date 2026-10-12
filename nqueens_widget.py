import sys
import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QFrame,
    QMessageBox,
)

from csp_solvers import (
    solve_backtracking,
    solve_mrv_forward_checking,
    solve_min_conflicts,
)


class NQueensWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mini Chess AI | N-Queens CSP")
        self.resize(1050, 760)

        self.n = 8
        self.solution = None
        self.cells = []

        self.setStyleSheet("""
            QWidget {
                background-color: #111318;
                color: #F1F3F5;
                font-family: Segoe UI;
                font-size: 14px;
            }

            QLabel#heading {
                font-size: 26px;
                font-weight: bold;
                color: #FF5364;
            }

            QFrame#panel {
                background-color: #1B1E26;
                border: 1px solid #303541;
                border-radius: 10px;
            }

            QPushButton {
                background-color: #292E39;
                border: 1px solid #3B4250;
                border-radius: 6px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #3A4252;
            }

            QPushButton#solve {
                background-color: #D94052;
                font-weight: bold;
            }

            QPushButton#solve:hover {
                background-color: #F04E61;
            }

            QComboBox, QSpinBox {
                background-color: #252A34;
                border: 1px solid #3B4250;
                border-radius: 5px;
                padding: 8px;
            }
        """)

        self.build_ui()
        self.create_board()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(16)

        heading = QLabel("N-QUEENS CSP VISUALIZER")
        heading.setObjectName("heading")

        subtitle = QLabel(
            "Constraint Satisfaction Problem • Algorithm Comparison"
        )
        subtitle.setStyleSheet("color: #AAB3C5;")

        root.addWidget(heading)
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(20)
        root.addLayout(content, 1)

        # LEFT: chessboard
        board_panel = QFrame()
        board_panel.setObjectName("panel")

        board_layout = QVBoxLayout(board_panel)
        board_layout.setContentsMargins(15, 15, 15, 15)

        board_title = QLabel("SOLUTION BOARD")
        board_title.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )
        board_layout.addWidget(board_title)

        self.board_container = QWidget()
        self.board_grid = QGridLayout(self.board_container)
        self.board_grid.setSpacing(2)

        board_layout.addWidget(self.board_container, 1)

        self.status_label = QLabel(
            "Choose an algorithm and click SOLVE."
        )
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #AAB3C5;")

        board_layout.addWidget(self.status_label)

        content.addWidget(board_panel, 3)

        # RIGHT: controls and statistics
        right_panel = QFrame()
        right_panel.setObjectName("panel")

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        controls_title = QLabel("SOLVER CONTROLS")
        controls_title.setStyleSheet(
            "font-size: 19px; font-weight: bold;"
        )
        right_layout.addWidget(controls_title)

        right_layout.addWidget(QLabel("Board size"))

        self.size_selector = QSpinBox()
        self.size_selector.setRange(4, 30)
        self.size_selector.setValue(8)
        self.size_selector.valueChanged.connect(self.change_size)

        right_layout.addWidget(self.size_selector)

        right_layout.addWidget(QLabel("Algorithm"))

        self.algorithm_selector = QComboBox()
        self.algorithm_selector.addItems([
            "Backtracking",
            "MRV + Forward Checking",
            "Min-Conflicts",
        ])

        right_layout.addWidget(self.algorithm_selector)

        self.solve_button = QPushButton("SOLVE N-QUEENS")
        self.solve_button.setObjectName("solve")
        self.solve_button.clicked.connect(self.solve)
        right_layout.addWidget(self.solve_button)

        self.clear_button = QPushButton("CLEAR BOARD")
        self.clear_button.clicked.connect(self.clear_board)
        right_layout.addWidget(self.clear_button)

        stats_title = QLabel("PERFORMANCE STATISTICS")
        stats_title.setStyleSheet(
            "font-size: 17px; font-weight: bold;"
        )
        right_layout.addWidget(stats_title)

        self.algorithm_result = self.make_stat_label(
            "Algorithm: —"
        )
        self.solved_result = self.make_stat_label(
            "Solved: —"
        )
        self.nodes_result = self.make_stat_label(
            "Nodes explored: —"
        )
        self.time_result = self.make_stat_label(
            "Execution time: —"
        )

        right_layout.addWidget(self.algorithm_result)
        right_layout.addWidget(self.solved_result)
        right_layout.addWidget(self.nodes_result)
        right_layout.addWidget(self.time_result)

        info = QLabel(
            "Goal:\n"
            "Place N queens on an N × N board so that "
            "no two queens share a row, column, or diagonal."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "color: #AAB3C5; padding-top: 10px;"
        )
        right_layout.addWidget(info)

        right_layout.addStretch()

        content.addWidget(right_panel, 2)

    def make_stat_label(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("""
            background-color: #252A34;
            border-radius: 6px;
            padding: 10px;
        """)
        return label

    def create_board(self):
        while self.board_grid.count():
            item = self.board_grid.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()

        self.cells = []

        for row in range(self.n):
            row_cells = []

            for col in range(self.n):
                cell = QPushButton("")
                cell.setMinimumSize(25, 25)

                cell.setFont(QFont("Segoe UI Symbol", 22))

                cell.setStyleSheet(
                    self.square_style(row, col, False)
                )

                self.board_grid.addWidget(cell, row, col)
                row_cells.append(cell)

            self.cells.append(row_cells)

        self.board_container.setMinimumSize(450, 450)

        self.update_board()

    def square_style(self, row, col, has_queen):
        if has_queen:
            background = "#B7D9A5"
            foreground = "#15221A"
        elif (row + col) % 2 == 0:
            background = "#E7DFC9"
            foreground = "#17202B"
        else:
            background = "#78966E"
            foreground = "#17202B"

        return f"""
            QPushButton {{
                background-color: {background};
                color: {foreground};
                border: none;
                border-radius: 0px;
                padding: 0px;
            }}

            QPushButton:hover {{
                border: 2px solid #FF5364;
            }}
        """

    def update_board(self):
        for row in range(self.n):
            for col in range(self.n):
                has_queen = (
                    self.solution is not None
                    and self.solution[row] == col
                )

                self.cells[row][col].setText(
                    "♛" if has_queen else ""
                )

                self.cells[row][col].setStyleSheet(
                    self.square_style(row, col, has_queen)
                )

    def change_size(self, value):
        self.n = value
        self.solution = None
        self.create_board()

        self.status_label.setText(
            f"Board resized to {self.n} × {self.n}."
        )

        self.reset_statistics()

    def reset_statistics(self):
        self.algorithm_result.setText("Algorithm: —")
        self.solved_result.setText("Solved: —")
        self.nodes_result.setText("Nodes explored: —")
        self.time_result.setText("Execution time: —")

    def clear_board(self):
        self.solution = None
        self.update_board()
        self.reset_statistics()

        self.status_label.setText(
            "Board cleared. Ready for a new solution."
        )

    def solve(self):
        algorithm = self.algorithm_selector.currentText()

        # Ordinary backtracking becomes expensive on large boards.
        if algorithm == "Backtracking" and self.n > 14:
            QMessageBox.warning(
                self,
                "Large board",
                "Backtracking can be slow for large boards. "
                "Choose MRV + Forward Checking or Min-Conflicts, "
                "or reduce the board size to 14 or less."
            )
            return

        self.solve_button.setEnabled(False)
        self.solve_button.setText("SOLVING...")

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()

            if algorithm == "Backtracking":
                result = solve_backtracking(self.n)

            elif algorithm == "MRV + Forward Checking":
                result = solve_mrv_forward_checking(self.n)

            else:
                result = solve_min_conflicts(
                    self.n,
                    max_steps=100000,
                    seed=42,
                )

            self.solution = result["solution"]
            self.update_board()

            self.algorithm_result.setText(
                f"Algorithm: {result['algorithm']}"
            )

            self.solved_result.setText(
                f"Solved: {'Yes' if result['solved'] else 'No'}"
            )

            self.nodes_result.setText(
                f"Nodes explored: {result['nodes']:,}"
            )

            self.time_result.setText(
                f"Execution time: {result['time']:.6f} seconds"
            )

            if result["solved"]:
                self.status_label.setText(
                    f"SUCCESS! A valid solution was found "
                    f"for N = {self.n}."
                )
            else:
                self.status_label.setText(
                    "No solution was found within the "
                    "algorithm's search limit."
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Solver error",
                str(error),
            )

        finally:
            QApplication.restoreOverrideCursor()
            self.solve_button.setEnabled(True)
            self.solve_button.setText("SOLVE N-QUEENS")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = NQueensWidget()
    window.show()

    sys.exit(app.exec())