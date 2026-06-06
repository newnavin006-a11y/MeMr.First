# PyChess

Simple Python chess game with optional time control and single-player AI (minimax).

Requirements
- Python 3.8+
- Install packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Run

```bash
python main.py
```

When started you'll be prompted to choose single-player, enable time control, seconds per side, and difficulty.

Notes
- Pieces are rendered with image-style chess piece icons.
- AI is a simple minimax material-evaluation engine. Increase difficulty for stronger play but expect slower moves.

Keyboard shortcuts
- **S**: Save current game to a timestamped PGN in `saved_games/`.
- **L**: Load the most recent PGN from `saved_games/`.
- **U**: Undo last move.
