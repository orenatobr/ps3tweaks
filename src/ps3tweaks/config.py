"""Configuration models and defaults for PS3 emulators."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class EmulatorConfig:
    """Store configuration values for one emulator profile.

    Attributes:
        emulator_type: Emulator binary identifier (for example, ``ps1_netemu.self``).
        memory_card_slot1: Memory card file name mapped to slot 1.
        video_mode: Video mode preset (for example, ``normal`` or ``fullscreen``).
        analog_mode: Whether analog input should be enabled.
        screen_size: Screen sizing preset used by the emulator.
    """

    emulator_type: str
    memory_card_slot1: str
    video_mode: str
    analog_mode: bool
    screen_size: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the configuration into a serializable dictionary.

        Returns:
            Dictionary representation of the current configuration.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmulatorConfig":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing all required ``EmulatorConfig`` fields.

        Returns:
            A new ``EmulatorConfig`` instance.
        """
        return cls(**data)


PS1_DEFAULT = EmulatorConfig(
    emulator_type="ps1_netemu.self",
    memory_card_slot1="PS1_slot1.vmc",
    video_mode="normal",
    analog_mode=True,
    screen_size="normal",
)

PS2_DEFAULT = EmulatorConfig(
    emulator_type="ps2_netemu.self",
    memory_card_slot1="PS2_slot1.vmc",
    video_mode="fullscreen",
    analog_mode=False,
    screen_size="fullscreen",
)
