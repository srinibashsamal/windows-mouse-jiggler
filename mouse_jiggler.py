import ctypes
import random
import time
import msvcrt
import sys

# Windows API Setup
user32 = ctypes.windll.user32

# --- Constants ---
STOP_KEYS = [b"q", b"x"]
PADDING = 0.1
MOVE_STEPS_MIN = 25
MOVE_STEPS_MAX = 45
MOVE_DURATION = 0.5
WAIT_MIN = 2.0  # seconds between moves
WAIT_MAX = 7.0
KEY_POLL_INTERVAL = 0.1


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_pos() -> tuple[int, int]:
    """Retrieves the current cursor position."""
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def get_screen_resolution() -> tuple[int, int]:
    """Returns the screen width and height."""
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def move_smooth(x2: int, y2: int, duration: float = MOVE_DURATION) -> None:
    """Moves the mouse smoothly from current position to (x2, y2)."""
    x1, y1 = get_pos()
    steps = random.randint(MOVE_STEPS_MIN, MOVE_STEPS_MAX)

    for i in range(1, steps + 1):
        t = i / steps
        # Linear interpolation with slight randomness
        target_x = int(x1 + (x2 - x1) * t) + random.randint(-1, 1)
        target_y = int(y1 + (y2 - y1) * t) + random.randint(-1, 1)

        user32.SetCursorPos(target_x, target_y)
        time.sleep(duration / steps)


def check_stop_key() -> bool:
    """Checks if a termination key has been pressed in the terminal."""
    if msvcrt.kbhit():
        key = msvcrt.getch().lower()
        if key in STOP_KEYS:
            print(f"\n\nStop key '{key.decode()}' pressed. Stopping.")
            return True
    return False


def format_elapsed(seconds: float) -> str:
    """Formats seconds into HH:MM:SS string."""
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(secs):02}"


def main():
    width, height = get_screen_resolution()
    start_time = time.time()

    print("--- Windows Mouse Jiggler ---")
    print(f"Detected Resolution: {width}x{height}")
    print("Keep this window in focus to use stop keys.")
    print("Press 'q' or 'x' to stop, or Ctrl+C to force quit.\n")

    try:
        while True:
            elapsed_str = format_elapsed(time.time() - start_time)
            sys.stdout.write(
                f"\rStatus: Moving | Uptime: {elapsed_str} | Press 'q' to quit..."
            )
            sys.stdout.flush()

            if check_stop_key():
                break

            # Calculate a random target within padded screen bounds
            target_x = random.randint(int(width * PADDING), int(width * (1 - PADDING)))
            target_y = random.randint(
                int(height * PADDING), int(height * (1 - PADDING))
            )

            move_smooth(target_x, target_y)

            # Wait period between movements
            wait_end = time.time() + random.uniform(WAIT_MIN, WAIT_MAX)
            while time.time() < wait_end:
                elapsed_str = format_elapsed(time.time() - start_time)
                sys.stdout.write(
                    f"\rStatus: Waiting| Uptime: {elapsed_str} | Press 'q' to quit..."
                )
                sys.stdout.flush()

                if check_stop_key():
                    return
                time.sleep(KEY_POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nStopped by keyboard interrupt (Ctrl+C).")


if __name__ == "__main__":
    main()
