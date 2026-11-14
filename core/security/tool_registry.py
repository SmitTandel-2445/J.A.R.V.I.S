"""
Tool Registry & Capability Catalog for J.A.R.V.I.S.
---------------------------------------------------
Centralizes all tools and system capabilities that J.A.R.V.I.S. or its AI brain
can invoke, categorized by execution capability and risk level.
Enforces least-privilege principles and prevents arbitrary tool invocation.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set
from core.security.action_classifier import RiskLevel


class ToolType(Enum):
    """Categorization of tool capabilities."""
    READ_ONLY = "READ_ONLY"
    WRITE = "WRITE"
    SYSTEM_CONTROL = "SYSTEM_CONTROL"
    DESTRUCTIVE = "DESTRUCTIVE"


@dataclass
class ToolDefinition:
    """Represents an authorized capability in J.A.R.V.I.S."""
    name: str
    description: str
    tool_type: ToolType
    default_risk: RiskLevel
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    is_enabled: bool = True


class ToolRegistry:
    """Central catalog of all authorized application and automation tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, tool: ToolDefinition) -> None:
        """Registers a tool definition."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Retrieves a registered tool definition."""
        return self._tools.get(name)

    def is_registered(self, name: str) -> bool:
        """Checks if a tool name is registered and authorized."""
        return name in self._tools and self._tools[name].is_enabled

    def list_tools(self) -> List[ToolDefinition]:
        """Returns all registered tools."""
        return list(self._tools.values())

    def _register_default_tools(self) -> None:
        """Populates the initial registry with J.A.R.V.I.S. core capabilities."""
        # Read-Only / Diagnostic Tools
        self.register(ToolDefinition(
            name="system_telemetry",
            description="Reads live CPU, RAM, and battery metrics.",
            tool_type=ToolType.READ_ONLY,
            default_risk=RiskLevel.LEVEL_1_LOW,
        ))
        self.register(ToolDefinition(
            name="time_date",
            description="Returns current system time and calendar date.",
            tool_type=ToolType.READ_ONLY,
            default_risk=RiskLevel.LEVEL_1_LOW,
        ))
        self.register(ToolDefinition(
            name="web_search",
            description="Searches Google for user queries.",
            tool_type=ToolType.READ_ONLY,
            default_risk=RiskLevel.LEVEL_1_LOW,
            required_params=["query"],
        ))
        self.register(ToolDefinition(
            name="clipboard_read",
            description="Reads the text currently stored in Windows clipboard.",
            tool_type=ToolType.READ_ONLY,
            default_risk=RiskLevel.LEVEL_1_LOW,
        ))

        # Safe Write & Navigation Tools
        self.register(ToolDefinition(
            name="open_app",
            description="Launches an approved local desktop or web application.",
            tool_type=ToolType.SYSTEM_CONTROL,
            default_risk=RiskLevel.LEVEL_2_MODERATE,
            required_params=["app_name"],
        ))
        self.register(ToolDefinition(
            name="window_control",
            description="Minimizes, maximizes, restores, or snaps application windows.",
            tool_type=ToolType.SYSTEM_CONTROL,
            default_risk=RiskLevel.LEVEL_2_MODERATE,
            required_params=["action"],
            optional_params=["app_name"],
        ))
        self.register(ToolDefinition(
            name="screenshot",
            description="Captures active desktop display and saves to Pictures.",
            tool_type=ToolType.WRITE,
            default_risk=RiskLevel.LEVEL_2_MODERATE,
        ))
        self.register(ToolDefinition(
            name="system_volume",
            description="Adjusts master system audio volume.",
            tool_type=ToolType.SYSTEM_CONTROL,
            default_risk=RiskLevel.LEVEL_1_LOW,
            required_params=["action"],
        ))
        self.register(ToolDefinition(
            name="system_brightness",
            description="Adjusts screen display brightness.",
            tool_type=ToolType.SYSTEM_CONTROL,
            default_risk=RiskLevel.LEVEL_1_LOW,
            required_params=["action"],
        ))

        # High-Risk & System State Tools
        self.register(ToolDefinition(
            name="create_folder",
            description="Creates a new directory on the user Desktop.",
            tool_type=ToolType.WRITE,
            default_risk=RiskLevel.LEVEL_3_HIGH,
            required_params=["folder_name"],
        ))
        self.register(ToolDefinition(
            name="system_power",
            description="Manages sleep, lock, and power state of the PC.",
            tool_type=ToolType.SYSTEM_CONTROL,
            default_risk=RiskLevel.LEVEL_3_HIGH,
            required_params=["action"],
        ))
        self.register(ToolDefinition(
            name="close_app",
            description="Closes or terminates a running application.",
            tool_type=ToolType.DESTRUCTIVE,
            default_risk=RiskLevel.LEVEL_3_HIGH,
            required_params=["app_name"],
        ))
        self.register(ToolDefinition(
            name="task_manager_kill",
            description="Forcefully terminates a specified process.",
            tool_type=ToolType.DESTRUCTIVE,
            default_risk=RiskLevel.LEVEL_3_HIGH,
            required_params=["target"],
        ))
        self.register(ToolDefinition(
            name="clipboard_type",
            description="Automates typing text into the focused active cursor.",
            tool_type=ToolType.WRITE,
            default_risk=RiskLevel.LEVEL_3_HIGH,
            required_params=["text"],
        ))

        # Critical Tools
        self.register(ToolDefinition(
            name="empty_recycle_bin",
            description="Permanently empties all deleted files from the Windows Recycle Bin.",
            tool_type=ToolType.DESTRUCTIVE,
            default_risk=RiskLevel.LEVEL_4_CRITICAL,
        ))


# Global default instance
tool_registry = ToolRegistry()

