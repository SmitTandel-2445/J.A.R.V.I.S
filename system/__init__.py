"""System Control Package for J.A.R.V.I.S."""
from system.audio_controller import AudioController, audio_controller
from system.brightness_controller import BrightnessController, brightness_controller
from system.display_controller import DisplayController, display_controller
from system.network_controller import NetworkController, network_controller
from system.power_controller import PowerController, power_controller
from system.task_manager import TaskManager, task_manager

__all__ = [
    "AudioController",
    "audio_controller",
    "BrightnessController",
    "brightness_controller",
    "DisplayController",
    "display_controller",
    "NetworkController",
    "network_controller",
    "PowerController",
    "power_controller",
    "TaskManager",
    "task_manager",
]
