import sys
import csv
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QMessageBox,
    QFrame,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from csp_solvers import (
    solve_backtracking,
    solve_mrv_forward_checking,
    solve_min_conflicts,
)


OUTPUT_FILE = Path("benchmark_results.csv")


class BenchmarkWorker(QThread):
    progress = Signal(str)
    result_ready = Signal(list)
    failed = Signal(str)

    def __init__(self, board_sizes):
        super().__init__()
        self.board_sizes = board_sizes

    def run(self):
        results = []

        solvers = [
            solve_backtracking,
            solve_mrv_forward_checking,
            solve_min_conflicts,
        ]

        try:
            total = len(self.board_sizes) * len(solvers)
            completed = 0

            for n in self.board_sizes:
                for solver in solvers:
                    if self.isInterruptionRequested():
                        return

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
                            "Success"
                            if result["solved"]
                            else "No solution found"
                        )

                    results.append(result)
                    completed += 1

                    self.progress.emit(
                        f"Testing N={n} | "
                        f"{result['algorithm']} | "
                        f"{completed}/{total}"
                    )

            self.result_ready.emit(results)

        except Exception as error:
            self.failed.emit(str(error))


class BenchmarkDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mini Chess AI | Benchmark Dashboard")
        self.resize(1250, 850)

        self.results = []
        self.worker = None

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #111318;
                color: #F1F3F5;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QLabel#title {
                color: #FF5364;
                font-size: 27px;
                font-weight: bold;
            }

            QFrame#panel {
                background-color: #1B1E26;
                border: 1px solid #303541;
                border-radius: 9px;
            }

            QPushButton {
                background-color: #292E39;
                border: 1px solid #3B4250;
                border-radius: 6px;
                padding: 9px 14px;
            }

            QPushButton:hover {
                background-color: #3A4252;
            }

            QPushButton#run {
                background-color: #D94052;
                font-weight: bold;
            }

            QComboBox {
                background-color: #252A34;
                border: 1px solid #3B4250;
                border-radius: 5px;
                padding: 7px;
            }

            QTableWidget {
                background-color: #1B1E26;
                gridline-color: #353B48;
                border: none;
            }

            QHeaderView::section {
                background-color: #292E39;
                padding: 7px;
                border: none;
                font-weight: bold;
            }

            QProgressBar {
                background-color: #252A34;
                border: none;
                border-radius: 4px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #D94052;
            }
        """)

        self.build_ui()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(13)

        title = QLabel("AI PERFORMANCE DASHBOARD")
        title.setObjectName("title")

        subtitle = QLabel(
            "N-Queens CSP | Algorithm benchmarking and comparison"
        )
        subtitle.setStyleSheet("color: #AAB3C5;")

        root.addWidget(title)
        root.addWidget(subtitle)

        # Controls
        controls = QFrame()
        controls.setObjectName("panel")

        control_layout = QHBoxLayout(controls)

        control_layout.addWidget(QLabel("Board sizes:"))

        self.size_selector = QComboBox()
        self.size_selector.addItems([
            "4, 8",
            "4, 8, 10, 12",
            "4, 8, 10, 12, 14",
            "4, 8, 10, 12, 14, 20, 30",
        ])
        self.size_selector.setCurrentIndex(1)

        control_layout.addWidget(self.size_selector)

        self.run_button = QPushButton("RUN BENCHMARKS")
        self.run_button.setObjectName("run")
        self.run_button.clicked.connect(self.run_benchmarks)

        control_layout.addWidget(self.run_button)

        self.export_button = QPushButton("EXPORT CSV")
        self.export_button.clicked.connect(self.export_csv)
        self.export_button.setEnabled(False)

        control_layout.addWidget(self.export_button)
        control_layout.addStretch()

        root.addWidget(controls)

        self.status_label = QLabel("Ready to run benchmarks.")
        self.status_label.setStyleSheet("color: #AAB3C5;")
        root.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)

        root.addWidget(self.progress_bar)

        # Summary cards
        cards = QHBoxLayout()

        self.total_label = self.make_card("TOTAL RUNS", "0")
        self.solved_label = self.make_card("SUCCESSFUL", "0")
        self.fastest_label = self.make_card("FASTEST RESULT", "—")

        cards.addWidget(self.total_label)
        cards.addWidget(self.solved_label)
        cards.addWidget(self.fastest_label)

        root.addLayout(cards)

        # Charts
        chart_panel = QFrame()
        chart_panel.setObjectName("panel")

        chart_layout = QVBoxLayout(chart_panel)

        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)

        chart_layout.addWidget(self.canvas)
        root.addWidget(chart_panel, 3)

        # Results table
        table_title = QLabel("BENCHMARK RESULTS")
        table_title.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )
        root.addWidget(table_title)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Board Size",
            "Algorithm",
            "Solved",
            "Nodes Explored",
            "Time (seconds)",
            "Status",
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        root.addWidget(self.table, 2)

    def make_card(self, heading, value):
        card = QFrame()
        card.setObjectName("panel")

        layout = QVBoxLayout(card)

        title = QLabel(heading)
        title.setStyleSheet(
            "color: #AAB3C5; font-size: 11px; font-weight: bold;"
        )

        value_label = QLabel(value)
        value_label.setStyleSheet(
            "font-size: 21px; font-weight: bold; color: #FF5364;"
        )

        layout.addWidget(title)
        layout.addWidget(value_label)

        card.value_label = value_label
        return card

    def run_benchmarks(self):
        text = self.size_selector.currentText()

        board_sizes = [
            int(value.strip())
            for value in text.split(",")
        ]

        self.run_button.setEnabled(False)
        self.export_button.setEnabled(False)

        self.status_label.setText("Starting benchmark tests...")
        self.progress_bar.setVisible(True)

        self.worker = BenchmarkWorker(board_sizes)
        self.worker.progress.connect(self.update_progress)
        self.worker.result_ready.connect(self.display_results)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def update_progress(self, message):
        self.status_label.setText(message)

    def display_results(self, results):
        self.results = results

        self.table.setRowCount(len(results))

        for row, result in enumerate(results):
            values = [
                f"{result['n']} × {result['n']}",
                result["algorithm"],
                "Yes" if result["solved"] else "No",
                f"{result['nodes']:,}",
                f"{result['time']:.6f}",
                result["status"],
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                self.table.setItem(row, column, item)

        successful = [
            result for result in results
            if result["solved"] and result["time"] > 0
        ]

        self.total_label.value_label.setText(str(len(results)))

        self.solved_label.value_label.setText(
            str(sum(result["solved"] for result in results))
        )

        if successful:
            fastest = min(successful, key=lambda item: item["time"])

            self.fastest_label.value_label.setText(
                f"{fastest['algorithm']} (N={fastest['n']})"
            )
        else:
            self.fastest_label.value_label.setText("—")

        self.draw_charts(results)

        self.export_button.setEnabled(bool(results))

        self.status_label.setText(
            f"Completed {len(results)} benchmark runs."
        )

    def draw_charts(self, results):
        self.figure.clear()

        time_ax = self.figure.add_subplot(121)
        nodes_ax = self.figure.add_subplot(122)

        algorithms = [
            "Backtracking",
            "MRV + Forward Checking",
            "Min-Conflicts",
        ]

        colors = [
            "#E85D75",
            "#55B8A9",
            "#6C91D9",
        ]

        sizes = sorted(set(result["n"] for result in results))

        width = 0.24
        x_positions = list(range(len(sizes)))

        for index, algorithm in enumerate(algorithms):
            times = []
            nodes = []

            for n in sizes:
                match = next(
                    (
                        result for result in results
                        if result["n"] == n
                        and result["algorithm"] == algorithm
                    ),
                    None,
                )

                if match and match["status"] != "Skipped (large search space)":
                    times.append(match["time"])
                    nodes.append(match["nodes"])
                else:
                    times.append(0)
                    nodes.append(0)

            offsets = [
                position + (index - 1) * width
                for position in x_positions
            ]

            time_ax.bar(
                offsets,
                times,
                width,
                label=algorithm,
                color=colors[index],
            )

            nodes_ax.bar(
                offsets,
                nodes,
                width,
                label=algorithm,
                color=colors[index],
            )

        time_ax.set_title("Execution Time")
        time_ax.set_xlabel("Board Size (N)")
        time_ax.set_ylabel("Seconds")
        time_ax.set_xticks(x_positions)
        time_ax.set_xticklabels(sizes)
        time_ax.legend(fontsize=7)
        time_ax.grid(axis="y", alpha=0.2)

        nodes_ax.set_title("Search Effort")
        nodes_ax.set_xlabel("Board Size (N)")
        nodes_ax.set_ylabel("Nodes Explored")
        nodes_ax.set_xticks(x_positions)
        nodes_ax.set_xticklabels(sizes)
        nodes_ax.legend(fontsize=7)
        nodes_ax.grid(axis="y", alpha=0.2)

        self.figure.tight_layout()
        self.canvas.draw()

    def export_csv(self):
        if not self.results:
            QMessageBox.information(
                self,
                "No results",
                "Run the benchmarks before exporting."
            )
            return

        try:
            columns = [
                "n",
                "algorithm",
                "solved",
                "nodes",
                "time",
                "status",
            ]

            with OUTPUT_FILE.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=columns,
                )

                writer.writeheader()

                for result in self.results:
                    writer.writerow({
                        column: result.get(column, "")
                        for column in columns
                    })

            QMessageBox.information(
                self,
                "Export successful",
                f"Results saved to:\n{OUTPUT_FILE.resolve()}",
            )

        except OSError as error:
            QMessageBox.critical(
                self,
                "Export failed",
                str(error),
            )

    def show_error(self, message):
        QMessageBox.critical(
            self,
            "Benchmark error",
            message,
        )

    def worker_finished(self):
        self.progress_bar.setVisible(False)
        self.run_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BenchmarkDashboard()
    window.show()

    sys.exit(app.exec())