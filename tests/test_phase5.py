import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.app_launcher import app_launcher
from automation.browser import browser_controller
from core.router import ActionRouter
from nlp.intent_classifier import IntentType
from system.audio_controller import audio_controller
from system.power_controller import power_controller


def test_phase5_automation():
    print("--- 1. Testing System Audio Controller ---")
    orig_vol = audio_controller.get_volume()
    print(f"Original Volume: {orig_vol}%")

    # Test setting volume
    target_vol = 75 if orig_vol != 75 else 80
    new_vol = audio_controller.set_volume(target_vol)
    print(f"Set Volume to: {new_vol}%")
    assert new_vol == target_vol

    # Test mute / unmute
    audio_controller.mute()
    assert audio_controller.is_muted() is True
    print("Mute test: SUCCESS")

    audio_controller.unmute()
    assert audio_controller.is_muted() is False
    print("Unmute test: SUCCESS")

    # Restore original volume
    audio_controller.set_volume(orig_vol)
    print(f"Restored Volume to: {orig_vol}%\n")

    print("--- 2. Testing App Launcher (Notepad) ---")
    # Resolve
    target = app_launcher.resolve_target("notepad")
    assert "notepad" in target.lower()
    print(f"Resolved 'notepad' to: '{target}'")

    # Launch Notepad
    success, msg = app_launcher.launch("notepad")
    print(f"Launch Notepad: {success} -> {msg}")
    assert success is True
    time.sleep(1)

    # Close Notepad
    close_success, close_msg = app_launcher.close("notepad")
    print(f"Close Notepad: {close_success} -> {close_msg}")
    assert close_success is True
    print("Notepad launch & close test: SUCCESS\n")

    print("--- 3. Testing Battery / Power Controller ---")
    bat_report = power_controller.get_battery_report()
    print(f"Battery Report: '{bat_report}'")
    assert len(bat_report) > 10
    print("Battery report test: SUCCESS\n")

    print("--- 4. Testing ActionRouter Integration for Phase 5 ---")
    router = ActionRouter()

    # Test Router with volume command
    res_vol = router.route("set volume to 80")
    print(f"Router Volume: {res_vol.spoken_response}")
    assert res_vol.intent == IntentType.SYSTEM_VOLUME

    # Test Router with battery command
    res_bat = router.route("check battery")
    print(f"Router Battery: {res_bat.spoken_response}")
    assert res_bat.intent == IntentType.SYSTEM_TELEMETRY

    # Restore original volume again
    audio_controller.set_volume(orig_vol)

    print("\nALL PHASE 5 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_phase5_automation()

