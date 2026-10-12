\# ♟️ Mini Chess AI and CSP Solver



An educational Artificial Intelligence project that combines a chess engine with Constraint Satisfaction Problem (CSP) solvers.



The project explores adversarial search, game-tree optimization, heuristic evaluation, and constraint-solving techniques through a Python-based implementation.



\## 📌 Project Overview



Mini Chess AI demonstrates how classical AI algorithms can be applied to strategic games and constraint-based problems.



The chess engine uses Negamax search and Alpha-Beta Pruning to explore candidate moves and evaluate chess positions. Additional modules provide CSP-solving functionality, benchmarking, and desktop application interfaces.



\## ✨ Features



\- ♟️ AI-based chess move selection

\- 🧠 Negamax search algorithm

\- ⚡ Alpha-Beta Pruning

\- 📊 Chess engine benchmarking

\- 🧩 Constraint Satisfaction Problem solvers

\- 👑 N-Queens problem component

\- 🖥️ Python desktop application

\- 🧪 Automated engine tests



> Note: Features should be considered complete only after their corresponding implementations have been tested.



\## 🛠️ Technologies Used



\- Python

\- python-chess

\- PySide6

\- Matplotlib

\- Git and GitHub



\## 🧠 AI Algorithms



\### 1. Negamax Search



Negamax is a variation of the Minimax algorithm that simplifies adversarial game-tree search by using the symmetry between two-player zero-sum games.



\### 2. Alpha-Beta Pruning



Alpha-Beta Pruning reduces the number of search nodes evaluated by eliminating branches that cannot influence the final decision.



\### 3. Heuristic Evaluation



The engine evaluates chess positions using heuristic criteria implemented in the evaluation function.



\### 4. Constraint Satisfaction Problems



The CSP modules explore problems involving variables, domains, and constraints. The project also includes an N-Queens component.



\## 📂 Project Structure



```text

Mini\_Chess\_AI\_CSP/

│

├── chess\_engine.py

├── desktop\_app.py

├── desktop\_app\_integrated.py

├── csp\_solvers.py

├── nqueens\_widget.py

├── benchmark\_dashboard.py

├── benchmarks.py

├── benchmark\_results.csv

├── rule\_reasoner.py

├── test\_engine.py

├── requirements.txt

├── .gitignore

└── README.md

