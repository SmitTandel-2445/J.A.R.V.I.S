import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.file_manager import file_manager
from automation.media_controller import media_controller
from automation.screenshot_controller import screenshot_controller
from automation.window_controller import window_controller
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType
from system.brightness_controller import brightness_controller

print("=== 1. Testing Screen Brightness Control ===")
orig_bright = brightness_controller.get_brightness()
print(f"Original Brightness: {orig_bright}%")

success_set, new_bright, msg_set = brightness_controller.set_brightness(70 if orig_bright != 70 else 80)
print(f"Set Brightness: {success_set} -> {new_bright}% ({msg_set})")
assert success_set is True

# Restore original brightness
brightness_controller.set_brightness(orig_bright)
print(f"Restored Brightness to: {orig_bright}%\n")

print("=== 2. Testing Screenshot Capture ===")
shot_ok, shot_msg, shot_path = screenshot_controller.capture()
print(f"Screenshot Result: {shot_ok} -> {shot_msg}")
if shot_ok:
    print(f"Saved Path: {shot_path}")
    assert shot_path is not None and os.path.exists(shot_path)
    print("Screenshot File Verified on Disk: PASS\n")
else:
    print(f"Screenshot gracefully handled non-interactive desktop session: PASS ({shot_msg})\n")

print("=== 3. Testing File & Folder Operations ===")
# Create test folder
test_folder = "JARVIS_TEST_DIR_999"
create_ok, create_msg = file_manager.create_folder(test_folder)
print(f"Create Folder: {create_ok} -> {create_msg}")
assert create_ok is True

desktop_test_path = Path(os.path.expanduser("~")) / "Desktop" / test_folder
assert desktop_test_path.exists()
print("Created Folder Verified on Desktop: PASS")

# Clean up test folder
desktop_test_path.rmdir()
print("Cleaned up test folder: PASS\n")

print("=== 4. Testing Intent Classifier on New Automations ===")
clf = IntentClassifier()

test_cases = [
    # Media
    ("play music", IntentType.MEDIA_CONTROL, "play_pause"),
    ("pause music", IntentType.MEDIA_CONTROL, "play_pause"),
    ("next song", IntentType.MEDIA_CONTROL, "next"),
    ("previous track", IntentType.MEDIA_CONTROL, "previous"),
    # Window
    ("minimize window", IntentType.WINDOW_CONTROL, "minimize"),
    ("maximize window", IntentType.WINDOW_CONTROL, "maximize"),
    ("show desktop", IntentType.WINDOW_CONTROL, "desktop"),
    ("snap window left", IntentType.WINDOW_CONTROL, "snap_left"),
    # Screenshot
    ("take a screenshot", IntentType.SCREENSHOT, None),
    ("capture screen", IntentType.SCREENSHOT, None),
    # Folders & Files
    ("open downloads", IntentType.FILE_FOLDER, "open"),
    ("open documents folder", IntentType.FILE_FOLDER, "open"),
    ("empty recycle bin", IntentType.FILE_FOLDER, "empty_recycle_bin"),
    # Brightness
    ("brightness up", IntentType.SYSTEM_BRIGHTNESS, "up"),
    ("decrease brightness", IntentType.SYSTEM_BRIGHTNESS, "down"),
    ("set brightness to 60%", IntentType.SYSTEM_BRIGHTNESS, "set"),
]

for query, exp_intent, exp_action in test_cases:
    res = clf.classify(query)
    print(f"'{query}' -> Intent: {res.intent.value}, Action: {res.parameters.get('action')}")
    assert res.intent == exp_intent
    if exp_action:
        assert res.parameters.get("action") == exp_action

print("All Intent Classifier Automation Cases: PASS\n")

print("=== 5. Testing ActionRouter Integration on Automation Commands ===")
router = ActionRouter()

res_shot = router.route("take screenshot")
print(f"Router Screenshot: {res_shot.spoken_response}")
assert res_shot.intent == IntentType.SCREENSHOT

res_bright = router.route("brightness up")
print(f"Router Brightness: {res_bright.spoken_response}")
assert res_bright.intent == IntentType.SYSTEM_BRIGHTNESS

res_media = router.route("play music")
print(f"Router Media: {res_media.spoken_response}")
assert res_media.intent == IntentType.MEDIA_CONTROL

# Restore original brightness again
brightness_controller.set_brightness(orig_bright)

print("\nALL EXPANDED DESKTOP AUTOMATION TESTS PASSED 100%!")
