#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows Mouse Jiggler
=====================

Moves the mouse with realistic curved motion so Windows (and most apps)
treat the session as active. Uses SendInput for genuine input events,
supports multi-monitor virtual desktops, is DPI-aware, and can also
prevent the system/display from sleeping.

Press 'q' or 'x' in the console window to stop, or Ctrl+C.
"""

import ctypes
import ctypes.wintypes as wintypes
import msvcrt
import random
import sys
import time

# ---------------------------------------------------------------------------
# DPI awareness – must be set before any screen-metric or cursor calls
# ---------------------------------------------------------------------------
try:
    # Prefer per-monitor DPI awareness (Windows 8.1+)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except (AttributeError, OSError):
    try:
        # Fallback for older Windows
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ---------------------------------------------------------------------------
# User-configurable settings
# ---------------------------------------------------------------------------
STOP_KEYS = (b"q", b"x")  # Keys that terminate the jiggler

PADDING = 0.05  # Keep this fraction of the desktop clear of edges
NEAR_MODE = True  # True → small moves near current cursor
NEAR_RADIUS = 250  # Max pixel distance of each move when NEAR_MODE is on

MOVE_STEPS_MIN = 30  # Minimum steps used for one smooth move
MOVE_STEPS_MAX = 60
MOVE_DURATION_MIN = 0.35  # Seconds a single move may take
MOVE_DURATION_MAX = 0.80
JITTER_PX = 1  # Random noise applied to intermediate steps
CURVE_STRENGTH = 0.25  # How strongly the Bezier path bends sideways

WAIT_MIN = 2.0  # Seconds to pause between moves
WAIT_MAX = 7.0
KEY_POLL_INTERVAL = 0.05  # How often we check for a stop key while waiting

KEEP_AWAKE = True  # Also block system sleep / display-off

# ---------------------------------------------------------------------------
# Win32 constants
# ---------------------------------------------------------------------------
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

ULONG_PTR = ctypes.c_size_t


# ---------------------------------------------------------------------------
# Win32 structures required by SendInput
# ---------------------------------------------------------------------------
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    """Union of the three possible input types – required for correct sizeof(INPUT)."""

    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUT_UNION),
    ]


# Tell ctypes the exact signature of the APIs we call
user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT

kernel32.SetThreadExecutionState.argtypes = (wintypes.DWORD,)
kernel32.SetThreadExecutionState.restype = wintypes.DWORD


# ---------------------------------------------------------------------------
# Low-level screen / cursor helpers
# ---------------------------------------------------------------------------
def get_virtual_screen() -> tuple[int, int, int, int]:
    """
    Return the bounding rectangle of the entire multi-monitor desktop.

    Returns
    -------
    left, top, width, height : int
        Origin and size of the virtual screen in pixels.
    """
    return (
        user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CYVIRTUALSCREEN),
    )


def get_cursor_pos() -> tuple[int, int]:
    """Return the current cursor position in screen coordinates."""
    point = POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def clamp(value: float, low: float, high: float) -> float:
    """Clamp *value* into the inclusive range [low, high]."""
    return max(low, min(high, value))


def send_absolute_move(x: int, y: int) -> None:
    """
    Move the cursor to absolute pixel coordinates (x, y) using SendInput.

    Coordinates are normalised to the 0–65535 range required by the
    MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK flags so that the move
    works correctly across multiple monitors.
    """
    left, top, width, height = get_virtual_screen()

    # Protect against a zero-sized desktop (should never happen)
    width = max(width - 1, 1)
    height = max(height - 1, 1)

    normalised_x = round((x - left) * 65535 / width)
    normalised_y = round((y - top) * 65535 / height)
    normalised_x = int(clamp(normalised_x, 0, 65535))
    normalised_y = int(clamp(normalised_y, 0, 65535))

    flags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    mouse_input = MOUSEINPUT(
        dx=normalised_x,
        dy=normalised_y,
        mouseData=0,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0,
    )
    input_event = INPUT(type=INPUT_MOUSE, mi=mouse_input)
    user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))


# ---------------------------------------------------------------------------
# Motion helpers – smooth, human-like paths
# ---------------------------------------------------------------------------
def smoothstep(t: float) -> float:
    """Hermite smooth-step: 0 → 0, 0.5 → 0.5, 1 → 1 with zero derivatives at ends."""
    return t * t * (3.0 - 2.0 * t)


def cubic_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    """Evaluate a cubic Bezier curve at parameter t ∈ [0, 1]."""
    u = 1.0 - t
    x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
    y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
    return x, y


def move_smooth(target_x: int, target_y: int) -> bool:
    """
    Move the cursor from its current position to (target_x, target_y)
    along an eased cubic Bezier curve with a gentle sideways bend.

    Returns
    -------
    bool
        True if the move completed normally, False if a stop key was pressed.
    """
    start_x, start_y = get_cursor_pos()
    delta_x = target_x - start_x
    delta_y = target_y - start_y
    distance = (delta_x * delta_x + delta_y * delta_y) ** 0.5

    if distance < 1.0:
        return True  # Already there – nothing to do

    # Unit vector perpendicular to the travel direction (used to bend the path)
    perp_x = -delta_y / distance
    perp_y = delta_x / distance
    bend_amount = distance * CURVE_STRENGTH

    def control_point(fraction: float) -> tuple[float, float]:
        """Create a control point offset sideways from the straight line."""
        offset = random.uniform(-bend_amount, bend_amount)
        return (
            start_x + delta_x * fraction + perp_x * offset,
            start_y + delta_y * fraction + perp_y * offset,
        )

    p0 = (start_x, start_y)
    p3 = (target_x, target_y)
    p1 = control_point(0.33)
    p2 = control_point(0.66)

    steps = random.randint(MOVE_STEPS_MIN, MOVE_STEPS_MAX)
    duration = random.uniform(MOVE_DURATION_MIN, MOVE_DURATION_MAX)
    step_delay = duration / steps

    for step in range(1, steps + 1):
        if check_stop_key():
            return False

        t = smoothstep(step / steps)
        x, y = cubic_bezier(p0, p1, p2, p3, t)

        # Add a little noise on intermediate steps; land exactly on target at the end
        if step < steps:
            x += random.randint(-JITTER_PX, JITTER_PX)
            y += random.randint(-JITTER_PX, JITTER_PX)
        else:
            x, y = target_x, target_y

        send_absolute_move(int(round(x)), int(round(y)))
        time.sleep(step_delay)

    return True


def pick_target() -> tuple[int, int]:
    """
    Choose the next destination inside the padded virtual desktop.

    When NEAR_MODE is enabled the target stays close to the current
    cursor position; otherwise a completely random point is chosen.
    """
    left, top, width, height = get_virtual_screen()

    min_x = left + width * PADDING
    max_x = left + width * (1.0 - PADDING)
    min_y = top + height * PADDING
    max_y = top + height * (1.0 - PADDING)

    if NEAR_MODE:
        cursor_x, cursor_y = get_cursor_pos()
        target_x = cursor_x + random.randint(-NEAR_RADIUS, NEAR_RADIUS)
        target_y = cursor_y + random.randint(-NEAR_RADIUS, NEAR_RADIUS)
        return (
            int(clamp(target_x, min_x, max_x)),
            int(clamp(target_y, min_y, max_y)),
        )

    return (
        int(random.uniform(min_x, max_x)),
        int(random.uniform(min_y, max_y)),
    )


# ---------------------------------------------------------------------------
# Console UI helpers
# ---------------------------------------------------------------------------
def check_stop_key() -> bool:
    """
    Return True if the user pressed a configured stop key in the console.

    Special (extended) keys that start with 0x00 or 0xE0 are consumed
    so they do not leave residual bytes in the input buffer.
    """
    while msvcrt.kbhit():
        key = msvcrt.getch()
        # Extended key prefix – discard the following scan-code byte
        if key in (b"\x00", b"\xe0"):
            msvcrt.getch()
            continue
        if key.lower() in STOP_KEYS:
            return True
    return False


def format_elapsed(seconds: float) -> str:
    """Format a duration in seconds as HH:MM:SS."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def show_status(state: str, start_time: float) -> None:
    """Overwrite the current console line with a short status message."""
    uptime = format_elapsed(time.time() - start_time)
    sys.stdout.write(f"\rStatus: {state:<7} | Uptime: {uptime} | Press 'q' to quit...")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    if sys.platform != "win32":
        sys.exit("This script only runs on Windows.")

    left, top, width, height = get_virtual_screen()
    start_time = time.time()

    print("--- Windows Mouse Jiggler ---")
    print(f"Virtual desktop : {width}×{height}  (origin {left}, {top})")
    print(f"Mode            : {'near cursor' if NEAR_MODE else 'full desktop'}")
    print("Keep this console window focused to use the stop keys.")
    print("Press 'q' or 'x' to stop, or Ctrl+C to force quit.\n")

    # Prevent the system and display from entering sleep while we run
    if KEEP_AWAKE:
        kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )

    try:
        while True:
            show_status("Moving", start_time)
            target = pick_target()
            if not move_smooth(*target):
                break

            # Random pause between moves
            wait_until = time.time() + random.uniform(WAIT_MIN, WAIT_MAX)
            while time.time() < wait_until:
                show_status("Waiting", start_time)
                if check_stop_key():
                    print("\n\nStop key pressed. Stopping.")
                    return
                time.sleep(KEY_POLL_INTERVAL)

        print("\n\nStop key pressed. Stopping.")

    except KeyboardInterrupt:
        print("\n\nStopped by keyboard interrupt (Ctrl+C).")

    finally:
        # Always restore normal power-management behaviour
        if KEEP_AWAKE:
            kernel32.SetThreadExecutionState(ES_CONTINUOUS)


if __name__ == "__main__":
    main()
