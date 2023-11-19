import keyboard
import os

def take_screenshot():
    # Create a flag file
    open("screenshot_flag.txt", "w").close()
    print("Screenshot hotkey pressed")

keyboard.add_hotkey('ctrl+p', take_screenshot)  # Using Ctrl+Shift+P to avoid common conflicts

keyboard.wait('esc')  # Wait until 'esc' is pressed to exit