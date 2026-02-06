import keyboard
import time
import threading
import os
import ctypes

# Win32 API Constants for Mouse (low-level, works with games)
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

# Low-level mouse functions (game compatible)
def move_mouse_relative(dx, dy):
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

def left_click(down):
    flags = MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP
    ctypes.windll.user32.mouse_event(flags, 0, 0, 0, 0)

def right_click(down):
    flags = MOUSEEVENTF_RIGHTDOWN if down else MOUSEEVENTF_RIGHTUP
    ctypes.windll.user32.mouse_event(flags, 0, 0, 0, 0)

def middle_click(down):
    flags = MOUSEEVENTF_MIDDLEDOWN if down else MOUSEEVENTF_MIDDLEUP
    ctypes.windll.user32.mouse_event(flags, 0, 0, 0, 0)

# Config
CONFIG_FILE = "config.txt"
STEP_SIZE = 10        # Starting speed (pixels per tick)
ACCEL_FACTOR = 1.05   # Acceleration multiplier
MAX_SPEED = 30        # Maximum speed (will be overridden by config)
DEFAULT_DELAY = 0.005 # Update rate (seconds)

def load_config():
    global MAX_SPEED
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                content = f.read().strip()
                MAX_SPEED = int(content)
                print(f"Loaded Speed from config: {MAX_SPEED}")
        else:
            print(f"Config file not found, creating default {CONFIG_FILE}")
            with open(CONFIG_FILE, 'w') as f:
                f.write("30")
            MAX_SPEED = 30
    except Exception as e:
        print(f"Error loading config: {e}")

load_config()

# Key Bindings
MOVE_UP = 'up'        # Arrow Up
MOVE_DOWN = 'down'    # Arrow Down
MOVE_LEFT = 'left'    # Arrow Left
MOVE_RIGHT = 'right'  # Arrow Right
TOGGLE_MODE = 'right shift'  # Right Shift to toggle mode

# Mouse click key aliases (keyboard library uses various names)
LEFT_CLICK_KEYS = {'left ctrl', 'left control', 'lctrl', 'ctrl'}
MIDDLE_CLICK_KEYS = {'left windows', 'left win', 'lwin', 'win'}
RIGHT_CLICK_KEYS = {'left alt', 'left menu', 'lalt', 'alt'}

# Mouse button states
left_pressed = False
middle_pressed = False
right_pressed = False

# Speed tracking
speeds = {
    'up': 0,
    'down': 0,
    'left': 0,
    'right': 0
}

# Active keys being held
active_keys = set()

# Mode (True = Mouse mode, False = Input mode)
mouse_mode = True

# Running flag
running = True

# Keys to suppress in mouse mode
MOVEMENT_KEYS = {MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT}
SUPPRESSED_KEYS = MOVEMENT_KEYS | LEFT_CLICK_KEYS | MIDDLE_CLICK_KEYS | RIGHT_CLICK_KEYS

def mouse_mover():
    """Thread for smooth mouse movement using low-level Win32 API"""
    global running, speeds, mouse_mode
    
    while running:
        if mouse_mode:
            dx = speeds['right'] - speeds['left']
            dy = speeds['down'] - speeds['up']
            
            if dx != 0 or dy != 0:
                move_mouse_relative(dx, dy)
        
        time.sleep(DEFAULT_DELAY)

def toggle_mode():
    """Toggle between mouse and input mode"""
    global mouse_mode, speeds, left_pressed, middle_pressed, right_pressed
    mouse_mode = not mouse_mode
    
    # Reset speeds
    for direction in speeds:
        speeds[direction] = 0
    
    # Release all mouse buttons
    if left_pressed:
        left_click(False)
        left_pressed = False
    if middle_pressed:
        middle_click(False)
        middle_pressed = False
    if right_pressed:
        right_click(False)
        right_pressed = False
    
    print(f"\nMode switched: {'MOUSE MODE' if mouse_mode else 'INPUT MODE'}")


def handle_key_event(event):
    """Handle key events with conditional suppression based on mouse mode"""
    global left_pressed, middle_pressed, right_pressed
    key = event.name.lower() if event.name else ''
    is_down = (event.event_type == 'down')
    
    # Only process suppressed keys
    if key not in SUPPRESSED_KEYS:
        return True  # Allow key through
    
    # In input mode, allow keys through
    if not mouse_mode:
        return True
    
    # In mouse mode - handle and suppress
    # Track active movement keys
    if key in MOVEMENT_KEYS:
        if is_down:
            active_keys.add(key)
        else:
            active_keys.discard(key)
    
    # Handle mouse clicks (check against all aliases)
    if key in LEFT_CLICK_KEYS:
        # Skip right ctrl
        if 'right' in key:
            return True
        if is_down and not left_pressed:
            left_click(True)
            left_pressed = True
        elif not is_down and left_pressed:
            left_click(False)
            left_pressed = False
    elif key in MIDDLE_CLICK_KEYS:
        # Skip right win
        if 'right' in key:
            return True
        if is_down and not middle_pressed:
            middle_click(True)
            middle_pressed = True
        elif not is_down and middle_pressed:
            middle_click(False)
            middle_pressed = False
    elif key in RIGHT_CLICK_KEYS:
        # Skip right alt
        if 'right' in key:
            return True
        if is_down and not right_pressed:
            right_click(True)
            right_pressed = True
        elif not is_down and right_pressed:
            right_click(False)
            right_pressed = False
    
    return False  # Suppress the key in mouse mode

# Track if toggle key was just pressed (debounce)
toggle_pressed = False

def handle_toggle(event):
    global toggle_pressed
    if event.event_type == 'down' and not toggle_pressed:
        toggle_pressed = True
        toggle_mode()
    elif event.event_type == 'up':
        toggle_pressed = False

# Register global hook for conditional suppression
keyboard.hook(handle_key_event, suppress=True)

# Toggle mode handler with debounce
keyboard.hook_key(TOGGLE_MODE, handle_toggle)

print("Arrow Clicker - Keyboard Mouse Control")
print("--------------------------")
print(f"Toggle Mode: {TOGGLE_MODE}")
print(f"Max Speed: {MAX_SPEED}")
print("MOUSE MODE Controls:")
print("  Arrow Keys   : Move Mouse")
print("  Left Ctrl    : Left Click")
print("  Start/Win    : Middle Click")
print("  Left Alt     : Right Click")
print("INPUT MODE: All keys work normally")
print("Close window to exit.")
print("--------------------------")
print("Current Mode: MOUSE MODE")

# Maus-Thread starten
mouse_thread = threading.Thread(target=mouse_mover)
mouse_thread.daemon = True
mouse_thread.start()

try:
    # Main loop
    while running:
        if mouse_mode:
            # Update speeds with acceleration for each direction
            for direction, key in [('up', MOVE_UP), ('down', MOVE_DOWN), ('left', MOVE_LEFT), ('right', MOVE_RIGHT)]:
                if key in active_keys:
                    if speeds[direction] == 0:
                        speeds[direction] = STEP_SIZE
                    else:
                        speeds[direction] = min(speeds[direction] * ACCEL_FACTOR, MAX_SPEED)
                else:
                    speeds[direction] = 0
        else:
            # Clear speeds when not in mouse mode
            for direction in speeds:
                speeds[direction] = 0
        
        time.sleep(DEFAULT_DELAY)
        
except KeyboardInterrupt:
    running = False
finally:
    # Clean exit
    running = False
    print("\nProgram ended.")
