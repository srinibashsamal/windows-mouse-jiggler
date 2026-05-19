# 🖱️ Windows Mouse Jiggler

A simple, lightweight Python utility that is a terminal-based mouse jiggler for Windows that simulates natural mouse movement to prevent your system from going idle or locking the screen by periodically moving the cursor.

---

## Features

- **Smooth, human-like movement**: interpolates cursor position with slight randomness to mimic real mouse usage.
- **Randomised Intervals**: Changes the wait time between moves to appear less like a bot.
- **Screen Awareness**: Automatically detects screen resolution and keeps movement within a padded boundary.
- **Configurable behaviour**: easily tune movement speed, step count, wait intervals, and screen padding via constants at the top of the script.
- **Live status display**: shows current status (Moving/Waiting) and uptime directly in the terminal.
- **Graceful exit**: press `q` or `x` to stop cleanly, or use `Ctrl+C` for a force quit
- **No dependencies**: uses only Python's standard library (`ctypes`, `msvcrt`, `random`, `time`, `sys`)

---

## Requirements

- **Operating System**: Windows (uses `ctypes.windll` and `msvcrt`)
- **Python**: 3.10 or higher (uses `tuple[int, int]` type hints)
- No external libraries required (uses built-in Python modules).

---

## Usage

1. Clone or download the repository.
2. Ensure you have Python installed.
3. Open a terminal or Command Prompt in the script's directory.
4. Run the script:
  ```bash
  python mouse_jiggler.py
  ```

5. Keep the terminal window **in focus** so stop-key polling works correctly.
6. Press **`q`** or **`x`** to stop, or **`Ctrl+C`** to force quit.

---

## Configuration

All tunable parameters are defined as constants near the top of the script:

| Constant            | Default  | Description                                          |
| ------------------- | -------- | ---------------------------------------------------- |
| `PADDING`           | `0.1`    | Fraction of screen edges to avoid (10% on each side) |
| `MOVE_STEPS_MIN`    | `25`     | Minimum interpolation steps per move                 |
| `MOVE_STEPS_MAX`    | `45`     | Maximum interpolation steps per move                 |
| `MOVE_DURATION`     | `0.5`    | Time (seconds) to complete one move                  |
| `WAIT_MIN`          | `2.0`    | Minimum wait time between moves (seconds)            |
| `WAIT_MAX`          | `7.0`    | Maximum wait time between moves (seconds)            |
| `KEY_POLL_INTERVAL` | `0.1`    | How often to check for stop keys (seconds)           |
| `STOP_KEYS`         | `q`, `x` | Keys that terminate the program                      |

---

## How It Works

1. The script detects your screen resolution using the Windows API.
2. It picks a random target coordinate within the padded screen bounds.
3. It moves the cursor smoothly to that target using linear interpolation with slight per-step randomness to appear more natural.
4. It waits a random interval before the next move.
5. Throughout, it continuously polls for a stop key in the terminal.

---

## Disclaimer

This tool is intended for **legitimate personal use** such as keeping a screen active during long downloads, presentations, or remote sessions. Please ensure its use complies with your organisation's IT and acceptable use policies.

---

## License

MIT License — feel free to use, modify, and distribute.
