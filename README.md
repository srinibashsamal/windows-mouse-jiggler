# 🖱️ Windows Mouse Jiggler

A lightweight, terminal-based mouse jiggler for Windows that simulates **realistic curved mouse movement** to prevent idle timeouts, screen locking, or status changes.

It uses proper `SendInput` events, supports multi-monitor setups, is DPI-aware, and can also keep the system and display from sleeping.

---

## Features

- **Human-like curved motion** – moves along eased cubic Bezier paths with gentle sideways bend and micro-jitter
- **Near-cursor mode** (default) – makes small, natural-looking moves around the current pointer instead of jumping across the whole desktop
- **Multi-monitor aware** – works correctly across the entire virtual desktop
- **DPI-aware** – handles high-DPI / scaled displays properly
- **Keep-awake** – optionally blocks system sleep and display turn-off while running
- **Fully configurable** – all behaviour controlled by constants at the top of the script
- **Live status** – shows current state (Moving / Waiting) and uptime in the terminal
- **Graceful exit** – press `q` or `x` to stop cleanly, or `Ctrl+C` for force quit
- **Zero dependencies** – uses only the Python standard library (`ctypes`, `msvcrt`, `random`, `time`, `sys`)

---

## Requirements

- **OS**: Windows (uses `ctypes.windll` and `msvcrt`)
- **Python**: 3.10 or higher
- No external libraries required (uses built-in Python modules)

---

## Usage

1. Clone or download the repository.
2. Open a terminal / Command Prompt in the project folder.
3. Run:

```bash
python mouse_jiggler.py
```

4. **Keep the terminal window focused** so the stop-key detection works.
5. Press **`q`** or **`x`** to stop, or **`Ctrl+C`** to force quit.

---

## Configuration

All settings are defined as constants near the top of `mouse_jiggler.py`:

| Constant            | Default  | Description                                                      |
| ------------------- | -------- | ---------------------------------------------------------------- |
| `STOP_KEYS`         | `q`, `x` | Keys that stop the jiggler                                       |
| `PADDING`           | `0.05`   | Fraction of the desktop edges to avoid (5% on each side)         |
| `NEAR_MODE`         | `True`   | `True` = small moves near current cursor; `False` = full desktop |
| `NEAR_RADIUS`       | `250`    | Max pixel distance of each move when `NEAR_MODE` is on           |
| `MOVE_STEPS_MIN`    | `30`     | Minimum interpolation steps per move                             |
| `MOVE_STEPS_MAX`    | `60`     | Maximum interpolation steps per move                             |
| `MOVE_DURATION_MIN` | `0.35`   | Minimum duration (seconds) of one move                           |
| `MOVE_DURATION_MAX` | `0.80`   | Maximum duration (seconds) of one move                           |
| `JITTER_PX`         | `1`      | Random noise applied to intermediate points                      |
| `CURVE_STRENGTH`    | `0.25`   | How strongly the Bezier path bends sideways                      |
| `WAIT_MIN`          | `2.0`    | Minimum pause between moves (seconds)                            |
| `WAIT_MAX`          | `7.0`    | Maximum pause between moves (seconds)                            |
| `KEY_POLL_INTERVAL` | `0.05`   | How often to check for stop keys while waiting                   |
| `KEEP_AWAKE`        | `True`   | Also prevent system sleep and display turn-off                   |

---

## How It Works

1. Detects the full virtual desktop (multi-monitor) and sets DPI awareness.
2. Optionally tells Windows to keep the system and display awake.
3. Repeatedly:
   - Picks a target (near the cursor or anywhere on the padded desktop).
   - Moves the cursor along a smooth cubic Bezier curve with easing and slight jitter.
   - Waits a random interval.
4. Continuously polls the console for the stop keys `q` / `x`.

All mouse movement is performed with genuine `SendInput` events so applications and the OS treat it as real user input.

---

## Disclaimer

This tool is intended for **legitimate personal use** only (e.g. long downloads, presentations, remote sessions).  
Please make sure its use complies with your organisation's IT and acceptable-use policies.

---

## License

MIT License — feel free to use, modify, and distribute.
